#!/usr/bin/python

from __future__ import print_function
import btrfs
import sys

fs = btrfs.FileSystem(sys.argv[1])
for device in fs.devices():
    print("dev item devid {0} total bytes {1} bytes used {2}".format(
        device.devid, device.total_bytes, device.bytes_used))

for chunk in fs.chunks():
    block_group = fs.block_group(chunk.vaddr)
    used = block_group.used
    used_pct = (used * 100) / chunk.length
    for i in xrange(len(chunk.stripes)):
        stripe = chunk.stripes[i]
        print("chunk vaddr {0} type {1} stripe {2} devid {3} offset {4} length {5} "
              "used {6} used_pct {7}".format(
                  chunk.vaddr,
                  btrfs.utils.block_group_flags_str(chunk.type),
                  i, stripe.devid, stripe.offset,
                  chunk.length, used, used_pct))
