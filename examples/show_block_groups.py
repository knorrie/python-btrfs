#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

with btrfs.FileSystem(sys.argv[1]) as fs:
    for chunk in fs.chunks():
        bg = fs.block_group(chunk.vaddr, chunk.length)
        print("block group offset {0:>13d} len {1:>10d} used {2:>10d} usage {3:>.2f} flags {4}"
            .format(bg.vaddr, bg.length, bg.used, bg.used_pct/100, bg.flags_str))
