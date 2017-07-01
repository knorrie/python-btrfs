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
        # directory can only have one link
        print(btrfs.ctree.InodeRefList(header, data)[0])
    elif header.type == btrfs.ctree.XATTR_ITEM_KEY:
        xattr_item_list = btrfs.ctree.XAttrItemList(header, data)
        print(xattr_item_list)
        for xattr_item in xattr_item_list:
            print("    {}".format(xattr_item))
    elif header.type == btrfs.ctree.DIR_ITEM_KEY:
        dir_item_list = btrfs.ctree.DirItemList(header, data)
        print(dir_item_list)
        for dir_item in dir_item_list:
            print("    {}".format(dir_item))
    elif header.type == btrfs.ctree.DIR_INDEX_KEY:
        print(btrfs.ctree.DirIndex(header, data))
    else:
        raise Exception("Whoa, key {}".format(btrfs.ctree.key_type_str(header.type)))

os.close(fd)
