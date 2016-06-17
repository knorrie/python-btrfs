#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)
print("block group vaddr {0} length {1} type {2}".format(
    vaddr, block_group.length, btrfs.utils.block_group_flags_str(block_group.flags),
))
for extent in fs.extents(vaddr, vaddr + block_group.length - 1):
    print("extent vaddr {0} length {1} refs {2} gen {3} flags {4}".format(
        extent.vaddr, extent.length, extent.refs, extent.generation,
        btrfs.utils.extent_flags_str(extent.flags),
    ))
    if extent.flags == btrfs.ctree.EXTENT_FLAG_DATA:
        for data_ref in extent.extent_data_refs:
            print("\textent data backref root {0} objectid {1} offset {2} count {3}".format(
                data_ref.root, data_ref.objectid, data_ref.offset, data_ref.count,
            ))
        for shared_ref in extent.shared_data_refs:
            print("\tshared data backref parent {0} count {1}".format(
                shared_ref.parent, shared_ref.count,
            ))
