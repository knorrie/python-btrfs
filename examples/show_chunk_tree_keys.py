#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
for device in fs.devices():
    print(device.key)
for chunk in fs.chunks():
    print(chunk.key)
