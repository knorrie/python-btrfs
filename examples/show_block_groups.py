#!/usr/bin/python3

import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])

for chunk in fs.chunks():
    print(fs.block_group(chunk.vaddr, chunk.length))
