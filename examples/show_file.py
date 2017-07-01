#!/usr/bin/python3

import btrfs
import os
import sys

if len(sys.argv) < 2:
    print("Usage: {} <file>".format(sys.argv[0]))
    sys.exit(1)

filename = sys.argv[1]

if not os.path.isfile(filename):
    print("{} is not a filename!".format(filename))
    sys.exit(1)

inum = os.stat(filename).st_ino
fd = os.open(filename, os.O_RDONLY)
tree, _ = btrfs.ioctl.ino_lookup(fd, objectid=inum)

print("filename {} tree {} inum {}".format(filename, tree, inum))

min_key = btrfs.ctree.Key(inum, 0, 0)
max_key = btrfs.ctree.Key(inum + 1, 0, 0) - 1
for header, data in btrfs.ioctl.search_v2(fd, tree, min_key, max_key):
    if header.type == btrfs.ctree.INODE_ITEM_KEY:
        print(btrfs.ctree.InodeItem(header, data))
    elif header.type == btrfs.ctree.INODE_REF_KEY:
        inode_ref_list = btrfs.ctree.InodeRefList(header, data)
        print(inode_ref_list)
        for inode_ref in inode_ref_list:
            print("    {}".format(inode_ref))
    elif header.type == btrfs.ctree.INODE_EXTREF_KEY:
        inode_extref_list = btrfs.ctree.InodeExtrefList(header, data)
        print(inode_extref_list)
        for inode_extref in inode_extref_list:
            print("    {}".format(inode_extref))
    elif header.type == btrfs.ctree.XATTR_ITEM_KEY:
        xattr_item_list = btrfs.ctree.XAttrItemList(header, data)
        print(xattr_item_list)
        for xattr_item in xattr_item_list:
            print("    {}".format(xattr_item))
    elif header.type == btrfs.ctree.EXTENT_DATA_KEY:
        print(btrfs.ctree.FileExtentItem(header, data))
    else:
        raise Exception("Whoa, key {}".format(btrfs.ctree.key_type_str(header.type)))

os.close(fd)
