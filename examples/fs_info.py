#!/usr/bin/python3

import btrfs
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

mountpoint = Path(sys.argv[1])
if not mountpoint.is_dir():
    print(f"Error: {mountpoint} is not a valid directory")
    sys.exit(1)

with btrfs.FileSystem(sys.argv[1]) as fs:
    fs_info = fs.fs_info()
    print(fs_info)
    for device in fs.devices():
        print(fs.dev_info(device.devid))
        print(fs.dev_stats(device.devid))
