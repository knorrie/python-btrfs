#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)
print("block group vaddr {0} length {1} type {2} {3}".format(
    vaddr, block_group.length,
    btrfs.utils.block_group_type_str(block_group.flags),
    btrfs.utils.block_group_profile_str(block_group.flags),
))
for extent in fs.extents(vaddr, vaddr + block_group.length - 1):
    print("extent vaddr {0} length {1} refs {2} gen {3} flags {4}".format(
        extent.vaddr, extent.length, extent.refs, extent.generation,
        btrfs.utils.extent_flags_str(extent.flags)
    ))
