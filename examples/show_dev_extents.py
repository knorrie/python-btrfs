#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

fs = btrfs.FileSystem(sys.argv[1])
chunks = {chunk.vaddr: chunk for chunk in fs.chunks()}
for d in fs.dev_extents():
    print("devid {} type {} pstart {} length {} pend {} vaddr {}".format(
        d.devid,
        btrfs.utils.block_group_flags_str(chunks[d.vaddr].type),
        d.paddr, d.length, d.paddr + d.length, d.vaddr
    ))
