#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
fs_info = fs.fs_info()
print(fs_info)
for device in fs.devices():
    print(fs.dev_info(device.devid))
    print(fs.dev_stats(device.devid))
