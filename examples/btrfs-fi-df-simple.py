#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys


for space in btrfs.FileSystem(sys.argv[1]).space_info():
    print(space)
