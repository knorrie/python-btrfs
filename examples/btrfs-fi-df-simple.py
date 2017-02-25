#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

for space in btrfs.FileSystem(sys.argv[1]).space_info():
    print(space)
