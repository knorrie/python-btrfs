#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 2:
    print("Usage: {} <text>".format(sys.argv[0]))
    sys.exit(1)

filename = sys.argv[1]
print(btrfs.crc32c.name_hash(filename))
