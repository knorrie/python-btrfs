#!/usr/bin/python3

import btrfs
import sys

tree = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])

for header, _ in btrfs.ioctl.search_v2(fs.fd, tree):
    print(btrfs.ctree.Key(header.objectid, header.type, header.offset))
