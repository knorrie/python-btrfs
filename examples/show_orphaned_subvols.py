#!/usr/bin/python3

import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
print(fs.orphan_subvol_ids())
