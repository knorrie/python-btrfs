#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 3:
    print("Usage: {} <tree> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

try:
    tree = int(sys.argv[1])
except ValueError:
    tree = {
        'root': btrfs.ctree.ROOT_TREE_OBJECTID,
        'extent': btrfs.ctree.EXTENT_TREE_OBJECTID,
        'chunk': btrfs.ctree.CHUNK_TREE_OBJECTID,
        'dev': btrfs.ctree.DEV_TREE_OBJECTID,
        'fs': btrfs.ctree.FS_TREE_OBJECTID,
        'csum': btrfs.ctree.CSUM_TREE_OBJECTID,
        'quota': btrfs.ctree.QUOTA_TREE_OBJECTID,
        'uuid': btrfs.ctree.UUID_TREE_OBJECTID,
        'free_space': btrfs.ctree.FREE_SPACE_TREE_OBJECTID,
        'tree_log': btrfs.ctree.TREE_LOG_OBJECTID,
        'tree_log_fixup': btrfs.ctree.TREE_LOG_FIXUP_OBJECTID,
        'tree_reloc': btrfs.ctree.TREE_RELOC_OBJECTID,
        'data_reloc': btrfs.ctree.DATA_RELOC_TREE_OBJECTID,
    }.get(sys.argv[1].lower(), None)
    if tree is None:
        print("ERROR: specify tree number or short name (e.g. root, extent, fs)")
        sys.exit(1)

fs = btrfs.FileSystem(sys.argv[2])
try:
    btrfs.utils.pretty_print(
        (btrfs.ctree.classify(header, data)
         for header, data in btrfs.ioctl.search_v2(fs.fd, tree))
    )
except FileNotFoundError:
    print("ERROR: tree {} does not exist".format(tree))
    sys.exit(1)
