#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 3:
    print("Usage: {} <vaddr> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

vaddr = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])
block_group = fs.block_group(vaddr)

for extent in fs.free_space_extents(min_vaddr=vaddr, max_vaddr=vaddr + block_group.length - 1):
    print(extent)
