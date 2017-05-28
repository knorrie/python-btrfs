#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 4:
    print("Usage: {} <subvolid> <inode> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

tree = int(sys.argv[1])
inum = int(sys.argv[2])
fs = btrfs.FileSystem(sys.argv[3])

min_key = btrfs.ctree.Key(inum, 0, 0)
max_key = btrfs.ctree.Key(inum + 1, 0, 0) - 1
for header, data in btrfs.ioctl.search_v2(fs.fd, tree, min_key, max_key):
    if header.type == btrfs.ctree.INODE_ITEM_KEY:
        print(btrfs.ctree.InodeItem(header, data))
    elif header.type == btrfs.ctree.INODE_REF_KEY:
        pos = 0
        while pos < header.len:
            ref = btrfs.ctree.InodeRef(header, data, pos)
            print(ref)
            pos += len(ref)
    elif header.type == btrfs.ctree.INODE_EXTREF_KEY:
        print(btrfs.ctree.InodeExtref(header, data))
    elif header.type == btrfs.ctree.XATTR_ITEM_KEY:
        print(btrfs.ctree.XAttrItem(header, data))
    elif header.type == btrfs.ctree.EXTENT_DATA_KEY:
        print(btrfs.ctree.FileExtentItem(header, data))
    else:
        raise Exception("Whoa, key {}".format(btrfs.ctree.key_type_str(header.type)))
