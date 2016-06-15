#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
print(fs.orphan_subvol_ids())
