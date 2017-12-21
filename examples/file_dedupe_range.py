#!/usr/bin/python3

import btrfs
import os
import sys

if len(sys.argv) < 6 or len(sys.argv[4:]) % 2 != 0:
    print("Usage: {} <src> <src_offset> <src_length> <dest> <dest_offset> "
          "[<dest> <dest_offset> ...]".format(sys.argv[0]))
    sys.exit(1)

src = sys.argv[1]
src_offset = int(sys.argv[2])
src_length = int(sys.argv[3])

if not os.path.isfile(src):
    print("{} is not a regular file!".format(src))
    sys.exit(1)

dest_names = []
range_infos = []
for n in range(4, len(sys.argv), 2):
    dest = sys.argv[n]
    if not os.path.isfile(dest):
        print("{} is not a regular file!".format(dest))
        sys.exit(1)
    dest_fd = os.open(dest, os.O_RDONLY)
    dest_offset = int(sys.argv[n+1])
    info = btrfs.ioctl.FileDedupeRangeInfo(dest_fd, dest_offset)
    dest_names.append(dest)
    range_infos.append(info)

fd = os.open(src, os.O_RDONLY)
try:
    btrfs.ioctl.fideduperange(fd, src_offset, src_length, range_infos)
    for dest, info in zip(dest_names, range_infos):
        print("dest {} {}".format(dest, info))
finally:
    os.close(fd)
    for info in range_infos:
        os.close(info.dest_fd)
