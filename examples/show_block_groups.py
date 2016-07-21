#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])

for chunk in fs.chunks():
    print(fs.block_group(chunk.vaddr, chunk.length))
