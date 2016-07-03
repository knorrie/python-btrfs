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
    elif isinstance(extent, btrfs.ctree.ExtentItem) and \
            extent.flags & btrfs.ctree.EXTENT_FLAG_TREE_BLOCK:
        print("    " + str(extent.tree_block_info))
        for tree_block_backref in extent.tree_block_info.tree_block_backrefs:
            print("    " + str(tree_block_backref))
        for shared_block_backref in extent.tree_block_info.shared_block_backrefs:
            print("    " + str(shared_block_backref))
    elif isinstance(extent, btrfs.ctree.MetaDataItem):
        for tree_block_backref in extent.tree_block_backrefs:
            print("    " + str(tree_block_backref))
        for shared_block_backref in extent.shared_block_backrefs:
            print("    " + str(shared_block_backref))
