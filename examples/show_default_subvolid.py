#!/usr/bin/python3

import btrfs
import sys
from btrfs.ctree import Key, DirItemList
from btrfs.ctree import ROOT_TREE_OBJECTID, ROOT_TREE_DIR_OBJECTID, DIR_ITEM_KEY, ULLONG_MAX

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

with btrfs.FileSystem(sys.argv[1]) as fs:
    tree = ROOT_TREE_OBJECTID
    min_key = Key(ROOT_TREE_DIR_OBJECTID, DIR_ITEM_KEY, 0)
    max_key = Key(ROOT_TREE_DIR_OBJECTID, DIR_ITEM_KEY, ULLONG_MAX)
    for header, data in btrfs.ioctl.search_v2(fs.fd, tree, min_key, max_key, nr_items=1):
        for dir_item in DirItemList(header, data):
            print(dir_item.location.objectid)
