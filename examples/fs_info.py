#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

fs = btrfs.FileSystem(sys.argv[1])
fs_info = fs.fs_info()
print(fs_info)
for device in fs.devices():
    print(fs.dev_info(device.devid))
    print(fs.dev_stats(device.devid))
