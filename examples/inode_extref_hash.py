#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 3:
    print("Usage: {} <parent_objectid> <name>".format(sys.argv[0]))
    sys.exit(1)

parent_objectid = int(sys.argv[1])
name = sys.argv[2]
print(btrfs.crc32c.extref_hash(parent_objectid, name))
