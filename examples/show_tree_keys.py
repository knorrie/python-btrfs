#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

tree = int(sys.argv[1])
fs = btrfs.FileSystem(sys.argv[2])

for header, _ in btrfs.ioctl.search(fs.fd, tree):
    print(btrfs.ctree.Key(header.objectid, header.type, header.offset))
