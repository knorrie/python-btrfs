#!/usr/bin/python3

import btrfs
import errno
import sys

if len(sys.argv) < 3:
    print("Usage: {} <vaddr> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)
print(block_group)

path_cache = {}

for extent in fs.extents(vaddr, vaddr + block_group.length - 1):
    if isinstance(extent, btrfs.ctree.ExtentItem) and extent.flags & btrfs.ctree.EXTENT_FLAG_DATA:
        print(extent)
        inodes, bytes_missed = btrfs.ioctl.logical_to_ino(fs.fd, extent.vaddr)
        for inode in inodes:
            if inode.root == btrfs.ctree.FS_TREE_OBJECTID or \
                (inode.root >= btrfs.ctree.FIRST_FREE_OBJECTID and
                 inode.root <= btrfs.ctree.LAST_FREE_OBJECTID):
                cache_key = (inode.root, inode.inum)
                if cache_key not in path_cache:
                    try:
                        path = btrfs.ioctl.ino_lookup(fs.fd, treeid=inode.root,
                                                      objectid=inode.inum)[1][:-1]
                        path_cache[cache_key] = btrfs.utils.embedded_text_for_str(path)
                    except IOError as e:
                        if e.errno == errno.ENOENT:
                            path_cache[cache_key] = None
                        else:
                            raise
                print("    root {} inode {} offset {} path {}".format(
                    inode.root, inode.inum, inode.offset, path_cache[cache_key]))
            else:
                print("    root {} inode {} offset {}".format(
                    inode.root, inode.inum, inode.offset))
        if bytes_missed > 0:
            print("    [...]")
