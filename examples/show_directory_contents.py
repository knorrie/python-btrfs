#!/usr/bin/python3

import btrfs
import os
import sys

if len(sys.argv) < 2:
    print("Usage: {} <directory>".format(sys.argv[0]))
    sys.exit(1)

dirname = sys.argv[1]

if not os.path.isdir(dirname):
    print("{} is not a directory!".format(dirname))
    sys.exit(1)

inum = os.stat(dirname).st_ino
fd = os.open(dirname, os.O_RDONLY)
tree, _ = btrfs.ioctl.ino_lookup(fd, objectid=inum)

print("directory {} tree {} inum {}".format(dirname, tree, inum))

min_key = btrfs.ctree.Key(inum, 0, 0)
max_key = btrfs.ctree.Key(inum + 1, 0, 0) - 1
for header, data in btrfs.ioctl.search_v2(fd, tree, min_key, max_key):
    if header.type == btrfs.ctree.INODE_ITEM_KEY:
        print(btrfs.ctree.InodeItem(header, data))
    elif header.type == btrfs.ctree.INODE_REF_KEY:
        # directory only has one link
        print(btrfs.ctree.InodeRef(header, data))
    elif header.type == btrfs.ctree.XATTR_ITEM_KEY:
        print(btrfs.ctree.XAttrItem(header, data))
    elif header.type == btrfs.ctree.DIR_ITEM_KEY:
        pos = 0
        while pos < header.len:
            item = btrfs.ctree.DirItem(header, data, pos)
            print(item)
            pos += len(item)
    elif header.type == btrfs.ctree.DIR_INDEX_KEY:
        print(btrfs.ctree.DirIndex(header, data))
    else:
        raise Exception("Whoa, key {}".format(btrfs.ctree.key_type_str(header.type)))

os.close(fd)
