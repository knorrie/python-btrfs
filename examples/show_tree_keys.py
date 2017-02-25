#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 3:
    print("Usage: {} <tree> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

tree = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])

for header, _ in btrfs.ioctl.search_v2(fs.fd, tree):
    print(btrfs.ctree.Key(header.objectid, header.type, header.offset))
