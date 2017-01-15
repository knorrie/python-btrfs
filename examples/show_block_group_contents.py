#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

load_data_refs = True
load_metadata_refs = True

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)
print(block_group)
for extent in fs.extents(vaddr, vaddr + block_group.length - 1,
                         load_data_refs, load_metadata_refs):
    print(extent)
    if isinstance(extent, btrfs.ctree.ExtentItem):
        if extent.flags & btrfs.ctree.EXTENT_FLAG_DATA and load_data_refs is True:
            for data_ref in extent.extent_data_refs:
                print("    " + str(data_ref))
            for shared_ref in extent.shared_data_refs:
                print("    " + str(shared_ref))
        elif extent.flags & btrfs.ctree.EXTENT_FLAG_TREE_BLOCK and load_metadata_refs is True:
            print("    " + str(extent.tree_block_info))
            for tree_block_backref in extent.tree_block_refs:
                print("    " + str(tree_block_backref))
            for shared_block_backref in extent.shared_block_refs:
                print("    " + str(shared_block_backref))
    elif isinstance(extent, btrfs.ctree.MetaDataItem) and load_metadata_refs is True:
        for tree_block_backref in extent.tree_block_refs:
            print("    " + str(tree_block_backref))
        for shared_block_backref in extent.shared_block_refs:
            print("    " + str(shared_block_backref))
