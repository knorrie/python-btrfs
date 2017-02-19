#!/usr/bin/python3

import btrfs
import sys


for space in btrfs.FileSystem(sys.argv[1]).space_info():
    print(space)
