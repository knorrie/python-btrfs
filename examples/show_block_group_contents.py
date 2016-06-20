#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)
print(block_group)
for extent in fs.extents(vaddr, vaddr + block_group.length - 1):
    print(extent)
    if extent.flags == btrfs.ctree.EXTENT_FLAG_DATA:
        for data_ref in extent.extent_data_refs:
            print("    " + str(data_ref))
        for shared_ref in extent.shared_data_refs:
            print("    " + str(shared_ref))
