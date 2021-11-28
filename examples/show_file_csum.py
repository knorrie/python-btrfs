#!/usr/bin/python3

import btrfs
import os
import struct
import sys
import textwrap

from btrfs.ctree import Key, EXTENT_DATA_KEY, FILE_EXTENT_REG, COMPRESS_NONE
from btrfs.ctree import CSUM_TREE_OBJECTID, EXTENT_CSUM_OBJECTID, EXTENT_CSUM_KEY
from btrfs.ctree import ULLONG_MAX

CSUM_SIZE = 4  # hardcoded to crc32c
csum_struct = struct.Struct('<L')
csum_function = btrfs.crc32c.crc32c_data

if len(sys.argv) < 2:
    print("Usage: {} <file>".format(sys.argv[0]))
    sys.exit(1)

filename = sys.argv[1]

if not os.path.isfile(filename):
    print("{} is not a regular file!".format(filename))
    sys.exit(1)


print("""------------------------------------- 8< --------------------------------------
The purpose of this example is to explore how checksums for data are stored
inside the checksum tree, and how to find a checksum for a given block of data.

The way in which checksums are looked up in here is clumsy and does not reflect
the way in which it happens in kernel code. E.g. the fact that we can only
search forward and not backwards in the trees limits the ability to quickly
look around and find the right csum item.

In order to make sure the example gets things right, we compare the checksum we
found against a computed checksum of the file data. To prevent the example code
from getting too complicated, we require the data extent not to be compressed.
Also, it has to be a regular extent, because inline extents are part of
metadata, which has the checksum stored inside the metadata block itself and
not in the checksum tree.

Keep in mind that this way of checking checksums does not make any sense except
for the purpose of the example here.  An online btrfs filesystem would never
allow us to read corrupted data. Also, the file we're looking at can use part
of a data block if it's at the end of the file.

Also, the ioctl interface is not able to tell us which checksum type is used
inside the filesystem.  In here's it's hardcoded to crc32c, because that's the
only available option in btrfs at this time.

------------------------------------- 8< --------------------------------------
""")


def wraprint(text):
    for line in textwrap.wrap(text, 80):
        print(line)
    print()


inum = os.stat(filename).st_ino
fd = os.open(filename, os.O_RDONLY)
tree, _ = btrfs.ioctl.ino_lookup(fd, objectid=inum)
os.close(fd)
wraprint("File {} has inode number {} in tree {}.".format(filename, inum, tree))

fs = btrfs.FileSystem(filename)


def first_regular_file_extent(inum, tree):
    min_key = Key(inum, EXTENT_DATA_KEY, 0)
    max_key = Key(inum, EXTENT_DATA_KEY + 1, 0) - 1
    for header, data in btrfs.ioctl.search_v2(fs.fd, tree, min_key, max_key):
        extent = btrfs.ctree.FileExtentItem(header, data)
        if extent.type == FILE_EXTENT_REG and extent.disk_bytenr != 0 \
                and extent.num_bytes >= fs.sectorsize and extent.compression == COMPRESS_NONE:
            return extent


wraprint("Looking for the first reference to a regular data extent that is at least "
         "sectorsize {} big and does not use compression...".format(fs.sectorsize))
extent = first_regular_file_extent(inum, tree)
if extent is None:
    wraprint("No regular extent found, try another file.")
    sys.exit()

wraprint("At offset {} in the file, it's using {} bytes of data which we can find at offset {} "
         "inside a data extent at vaddr {}.".format(
             extent.logical_offset, extent.num_bytes, extent.offset, extent.disk_bytenr))

vaddr = extent.disk_bytenr + extent.offset

wraprint("Now, we first look up the checksum value for one block ({} bytes) "
         "of data at vaddr {} ({} + {}).".format(
             fs.sectorsize, vaddr, extent.disk_bytenr, extent.offset))
wraprint("If we're lucky, the checksum tree has a key at {}. "
         "If not, we have to try searching back a bit to find the csum object that "
         "holds information about our data block. Searching back is done in a very clumsy "
         "way, because we can only search forward when using the search ioctl.".format(vaddr))


def search_extent_csum_after(vaddr, min_vaddr):
    if min_vaddr < 0:
        min_vaddr = 0
    min_key = Key(EXTENT_CSUM_OBJECTID, EXTENT_CSUM_KEY, min_vaddr)
    max_key = Key(EXTENT_CSUM_OBJECTID, EXTENT_CSUM_KEY, ULLONG_MAX)
    prev_header = None
    prev_data = None
    for header, data in btrfs.ioctl.search_v2(fs.fd, CSUM_TREE_OBJECTID, min_key, max_key):
        if header.offset > vaddr:
            if prev_header is not None:
                return prev_header, prev_data
            return header, data
        prev_header, prev_data = header, data
    return prev_header, prev_data


def search_extent_csum_for(vaddr):
    min_vaddr = vaddr
    header, data = search_extent_csum_after(vaddr, min_vaddr)
    look_back = 4096
    while header is None or header.offset > vaddr:
        print("Next found extent csum at {} is {}.".format(min_vaddr, header.offset))
        print("Restarting search {} bytes before our target vaddr.".format(
            btrfs.utils.pretty_size(look_back)))
        min_vaddr = vaddr-look_back
        header, data = search_extent_csum_after(vaddr, min_vaddr)
        look_back = look_back * 2
    print()
    return header, data


header, data = search_extent_csum_for(vaddr)
csum_covers_vaddr_start = header.offset
nr_csums = header.len // CSUM_SIZE
csum_covers_vaddr_end = header.offset + nr_csums * fs.sectorsize

if vaddr < csum_covers_vaddr_start or vaddr + fs.sectorsize > csum_covers_vaddr_end:
    wraprint("BUG: we got a csum extent that does not cover our block: "
             "[{},{}). The range covered by the csum object is: [{},{}).".format(
                vaddr, vaddr + fs.sectorsize, csum_covers_vaddr_start, csum_covers_vaddr_end))
    sys.exit(1)

wraprint("We found an item holding {} bytes of checksums, starting at vaddr {}. "
         "This means it contains {} {}-byte checksums covering a range up to but not including "
         "vaddr {}.".format(header.len, csum_covers_vaddr_start,
                            nr_csums, CSUM_SIZE, csum_covers_vaddr_end))

index_in_csum_data = (vaddr - header.offset) // fs.sectorsize
offset_in_csum_data = index_in_csum_data * CSUM_SIZE
stored_csum, = csum_struct.unpack_from(data, offset_in_csum_data)

wraprint("The checksum for our example data block is item nr {} at byte position {}. The checksum "
         "value is {}".format(index_in_csum_data, offset_in_csum_data, stored_csum))

with open(filename, 'rb') as f:
    f.seek(extent.logical_offset)
    computed_csum = csum_function(f.read(fs.sectorsize))

    wraprint("The checksum computed from reading {} bytes from the file "
             "at position {} is: {}".format(fs.sectorsize, extent.logical_offset, computed_csum))

print("""------------------------------------- 8< --------------------------------------
If the above checksum values match, then Yay.

If not, then either it means this example program has a bug, or it means you've
hit one of the many possible small and large race conditions involved here if
you're trying this on an actively used filesystem.
------------------------------------- 8< --------------------------------------
""")
