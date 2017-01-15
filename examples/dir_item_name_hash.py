#!/usr/bin/python

from __future__ import division, print_function, absolute_import, unicode_literals
import btrfs
import sys

filename = sys.argv[1]
print(btrfs.crc32c.name_hash(filename))
