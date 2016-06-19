#!/usr/bin/python

from __future__ import print_function
from collections import deque
import btrfs
import sys


def colours():
    colours = deque([
        '33FF33', '00CC00',  # green
        'FFFF33', 'CCCC00',  # yellow
        '3399FF', '0000CC',  # blue
        'FF3333', 'CC0000',  # red
        'FF33FF', 'CC00CC',  # purple
    ])
    while True:
        yield colours[0]
        colours.rotate(-1)


def draw_type():
    yield 'AREA'
    while True:
        yield 'STACK'


def munin_config(fs, spaces, used_types, check_wasted):
    print("multigraph btrfs_usage_{0}".format(str(fs.fsid).replace('-', '_')))
    print("graph_args --base 1024 -l 0")
    print("graph_vlabel bytes")
    print("graph_title btrfs space usage for {0}".format(fs.path))
    print("graph_category disk")
    print("graph_info This graph shows how btrfs uses available space")
    draw = draw_type()
    colour = colours()
    for _type in used_types:
        label = btrfs.utils.block_group_flags_str(_type).lower().replace('|', '_')
        description = btrfs.utils.block_group_type_str(_type)
        print("{0}_used.label Used {1}".format(label, description))
        print("{0}_used.draw {1}".format(label, next(draw)))
        print("{0}_used.info Used {1}".format(label, description))
        print("{0}_used.colour {1}".format(label, next(colour)))
        print("{0}_unused.label Unused {1}".format(label, description))
        print("{0}_unused.draw {1}".format(label, next(draw)))
        print("{0}_unused.info Unused {1}".format(label, description))
        print("{0}_unused.colour {1}".format(label, next(colour)))
    print("unallocated.label Unallocated")
    print("unallocated.draw STACK")
    print("unallocated.info Not allocated raw space")
    print("unallocated.colour FFFFFF")
    if check_wasted:
        print("wasted_soft.label Reclaimable non-alloc")
        print("wasted_soft.draw STACK")
        print("wasted_soft.info Reclaimable not allocatable")
        print("wasted_soft.colour BBBBBB")
        print("wasted_hard.label Non-allocatable")
        print("wasted_hard.draw STACK")
        print("wasted_hard.info Non-allocatable")
        print("wasted_hard.colour 888888")
    print("total.label Total")
    print("total.draw LINE2")
    print("total.info Total raw space")
    print("total.colour 000000")
    print("")


def munin_values(fs, spaces, used_types, check_wasted):
    print("multigraph btrfs_usage_{0}".format(str(fs.fsid).replace('-', '_')))
    for _type in used_types:
        label = btrfs.utils.block_group_flags_str(_type).lower().replace('|', '_')
        used = 0
        allocated = 0
        for space in spaces:
            if space.type == _type:
                used += space.raw_used_bytes
                allocated += space.raw_total_bytes
        print("{0}_used.value {1}".format(label, used))
        print("{0}_unused.value {1}".format(label, allocated - used))
    devices = list(fs.devices())
    device_total = [device.total_bytes for device in devices]
    device_unallocated = [device.total_bytes - device.bytes_used for device in devices]
    if check_wasted:
        wasted_total = btrfs.utils.wasted_space_raid1(device_unallocated)
        wasted_hard = btrfs.utils.wasted_space_raid1(device_total)
        wasted_soft = wasted_total - wasted_hard
        unallocated = sum(device_unallocated) - wasted_total
        print("unallocated.value {0}".format(unallocated))
        print("wasted_soft.value {0}".format(wasted_soft))
        print("wasted_hard.value {0}".format(wasted_hard))
    else:
        unallocated = sum(device_unallocated)
        print("unallocated.value {0}".format(unallocated))
    total = sum(device_total)
    print("total.value {0}".format(total))
    print("")


def main():
    for fs in btrfs.utils.mounted_filesystems():
        spaces = fs.space_info()
        used_types = []
        for space in spaces:
            if space.type not in used_types and space.type != btrfs.SPACE_INFO_GLOBAL_RSV:
                used_types.append(space.type)
        flags_raid1_data = (btrfs.BLOCK_GROUP_DATA | btrfs.BLOCK_GROUP_RAID1)
        check_wasted = any([space.flags & flags_raid1_data == flags_raid1_data
                           for space in spaces])

        if len(sys.argv) > 1 and sys.argv[1] == "config":
            munin_config(fs, spaces, used_types, check_wasted)
        else:
            munin_values(fs, spaces, used_types, check_wasted)

if __name__ == "__main__":
    main()
