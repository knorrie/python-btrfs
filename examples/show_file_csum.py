#!/usr/bin/python3

import btrfs
import os
import sys

if len(sys.argv) < 2:
    print("Usage: {} <file>".format(sys.argv[0]))
    sys.exit(1)

filename = sys.argv[1]

if not os.path.isfile(filename):
    print("{} is not a filename!".format(filename))
    sys.exit(1)

inum = os.stat(filename).st_ino
fd = os.open(filename, os.O_RDONLY)
tree, _ = btrfs.ioctl.ino_lookup(fd, objectid=inum)

print("filename {} tree {} inum {} file".format(filename, tree, inum, ))

min_key = btrfs.ctree.Key(inum, 0, 0)
max_key = btrfs.ctree.Key(inum + 1, 0, 0) - 1
file_extent_offsets = []
#get the extents
for header, data in btrfs.ioctl.search_v2(fd, tree, min_key, max_key):
	if header.type == btrfs.ctree.EXTENT_DATA_KEY:
		data_extent = btrfs.ctree.FileExtentItem(header, data)
		file_extent_offsets.append((data_extent.disk_bytenr, data_extent.disk_num_bytes))
		print("Found data extent starting at {}".format(data_extent.disk_bytenr))

#
for offset in file_extent_offsets:
	start = offset[0]
	end = start + offset[1]
	#Since checksums are calculated every 4k (sector size) we can calculate how many
	#checksums are required to cover the whole extent
	total_csums = (end - start) // 4096

#	key = btrfs.ctree.Key(btrfs.ctree.EXTENT_CSUM_OBJECTID, btrfs.ctree.EXTENT_CSUM_KEY, start)
#	max_key = btrfs.ctree.Key(btrfs.ctree.EXTENT_CSUM_OBJECTID, btrfs.ctree.EXTENT_CSUM_KEY, start + extent_len)

	for header, data in btrfs.ioctl.search_v2(fd, btrfs.ctree.CSUM_TREE_OBJECTID, buf_size=):
		#how many checksums are in this item
		checksum_count = header.len // 4
		#The range checksums in this item cover
		checksum_start = header.offset
		checksum_end = checksum_start + (checksum_count * 4096)

		if start >= header.offset and end <= checksum_end and total_csums > 0:
			print("objectid={} type={} offset={} item size={}".format(header.objectid, header.type, header.offset, header.len))

			#how far in this checksum item do we begin. First we find how many 4kb blocks in are we
			checksum_offset = ((start - checksum_start) // 4096)
			#Then we convert to bytes, each checksum is 4bytes (u32)
			checksum_offset *= 4
			#checksums in the current item
			checksum_count = header.len // 4
			if checksum_count > total_csums:
				#there are csums for different items in this csum item
				for i in range(total_csums):
					csum_start_pos = checksum_offset + i*4
					checksum = int.from_bytes(data[csum_start_pos:csum_start_pos+4], "little")
					print("0x{:x}".format(checksum))
					total_csums -= total_csums
			else:
				for i in range(0, header.len, 4):
					checksum = int.from_bytes(data[i:i+4], "little")
					print("0x{:x}".format(checksum))
					total_csums -= checksum_count


os.close(fd)
