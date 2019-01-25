#!/usr/bin/python3

import btrfs
import os
import sys
import uuid

if len(sys.argv) < 5:
    print("Usage: {} <received-uuid> <stransid> <stime> <snapshot>".format(sys.argv[0]))
    print("Example: {} 00000000-1234-5678-90ab-cdef00000000 "
          "31337 1234.5678 /path/to/snapshot".format(sys.argv[0]))
    sys.exit(1)

received_uuid = uuid.UUID(sys.argv[1])
stransid = int(sys.argv[2])
stime_sec, stime_nsec = [int(x) for x in sys.argv[3].split('.')]
stime = btrfs.ctree.TimeSpec.from_values(stime_sec, stime_nsec)
subvol_path = sys.argv[4]

inum = os.stat(subvol_path).st_ino
if inum != 256:
    print("{} is not the start of a subvolume (inum {} != 256)".format(subvol_path, inum))
    sys.exit(1)

subvol_fd = os.open(subvol_path, os.O_RDONLY)
tree, _ = btrfs.ioctl.ino_lookup(subvol_fd)


def print_subvol_info(root):
    print("  subvol_id: {}".format(root.key.objectid))
    print("  received_uuid: {}".format(root.received_uuid))
    print("  stime: {}".format(root.stime))
    print("  stransid: {}".format(root.stransid))
    print("  rtime: {}".format(root.rtime))
    print("  rtransid: {}".format(root.rtransid))
    print()


with btrfs.FileSystem(subvol_path) as fs:
    print("Current subvolume information:")
    root = list(fs.subvolumes(min_id=tree, max_id=tree))[0]
    print_subvol_info(root)

    print("Setting received subvolume...")
    print()
    rtransid, rtime = btrfs.ioctl.set_received_subvol(subvol_fd, received_uuid, stransid, stime)
    os.close(subvol_fd)

    print("Resulting subvolume information:")
    root = list(fs.subvolumes(min_id=tree, max_id=tree))[0]
    print_subvol_info(root)
