#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])

for device in fs.devices():
    print(device)

for chunk in fs.chunks():
    print(fs.block_group(chunk.vaddr, chunk.length))
    print("    " + str(chunk))
    for stripe in chunk.stripes:
        print("        " + str(stripe))
