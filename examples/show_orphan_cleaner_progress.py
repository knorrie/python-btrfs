#!/usr/bin/python3

import btrfs
import sys
import time

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

report_interval = 120
zero_key = btrfs.ctree.Key(0, 0, 0)
prev_amount_orphans_left = -1

fs = btrfs.FileSystem(sys.argv[1])
while True:
    current_id = None
    orphans = fs.orphan_subvol_ids()
    amount_orphans_left = len(orphans)
    if prev_amount_orphans_left != amount_orphans_left:
        print("{} orphans left to clean".format(amount_orphans_left))
        prev_amount_orphans_left = amount_orphans_left
    for subvol_id in orphans:
        subvolumes = list(fs.subvolumes(min_id=subvol_id, max_id=subvol_id))
        if len(subvolumes) == 0:
            continue
        subvol = subvolumes[0]
        if subvol.drop_progress != zero_key:
            current_id, since = subvol_id, int(time.time())
            break
    if current_id is not None:
        report_after = 0
        while True:
            subvolumes = list(fs.subvolumes(min_id=current_id, max_id=current_id))
            duration = int(time.time()) - since
            if len(subvolumes) == 0:
                if report_after > 0:
                    print("dropping root {} finished after at least {} sec".format(
                        current_id, duration))
                break
            if duration >= report_after:
                subvol = subvolumes[0]
                print("dropping root {} for at least {} sec drop_progress {}".format(
                    current_id, duration, subvol.drop_progress))
                report_after += report_interval
            time.sleep(1)
    else:
        time.sleep(1)
