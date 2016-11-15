#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
chunks = {chunk.vaddr: chunk for chunk in fs.chunks()}
for d in fs.dev_extents():
    print("devid {0} type {1} pstart {2} length {3} pend {4} vaddr {5}".format(
        d.devid,
        btrfs.utils.block_group_flags_str(chunks[d.vaddr].type),
        d.paddr, d.length, d.paddr + d.length, d.vaddr
    ))
