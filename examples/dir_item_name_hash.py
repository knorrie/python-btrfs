#!/usr/bin/python3

import btrfs
import sys

filename = sys.argv[1]
print(btrfs.crc32c.name_hash(filename))
