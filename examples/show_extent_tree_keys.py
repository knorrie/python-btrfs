#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)

tree = btrfs.ctree.EXTENT_TREE_OBJECTID
min_key = btrfs.ctree.Key(vaddr, 0, 0)
max_key = btrfs.ctree.Key(vaddr + block_group.length, 0, 0) - 1
for header, _ in btrfs.ioctl.search(fs.fd, tree, min_key, max_key):
    print(btrfs.ctree.Key(header.objectid, header.type, header.offset))
