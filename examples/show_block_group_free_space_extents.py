#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 3:
    print("Usage: {} <vaddr> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

vaddr = int(sys.argv[1])
with btrfs.FileSystem(sys.argv[2]) as fs:
    block_group = fs.block_group(vaddr)

    try:
        for extent in fs.free_space_extents(min_vaddr=vaddr,
                                            max_vaddr=vaddr + block_group.length - 1):
            print(extent)
    except FileNotFoundError:
        print("No Free Space Tree? To run this example you need space_cache=v2")
        sys.exit(1)
