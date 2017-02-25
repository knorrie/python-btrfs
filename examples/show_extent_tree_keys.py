#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 3:
    print("Usage: {} <vaddr> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)

tree = btrfs.ctree.EXTENT_TREE_OBJECTID
min_key = btrfs.ctree.Key(vaddr, 0, 0)
max_key = btrfs.ctree.Key(vaddr + block_group.length, 0, 0) - 1
for header, _ in btrfs.ioctl.search_v2(fs.fd, tree, min_key, max_key):
    print(btrfs.ctree.Key(header.objectid, header.type, header.offset))
