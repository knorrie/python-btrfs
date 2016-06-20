#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
tree = btrfs.ctree.CHUNK_TREE_OBJECTID
min_key = btrfs.ctree.Key(0, 0, 0)
max_key = btrfs.ctree.Key(btrfs.ioctl.ULLONG_MAX, 255, btrfs.ioctl.ULLONG_MAX)
for header, _ in btrfs.ioctl.search(fs.fd, tree, min_key, max_key):
    print(btrfs.ctree.Key(header.objectid, header.type, header.offset))
