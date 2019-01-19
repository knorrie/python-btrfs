#!/usr/bin/python3

import btrfs
import sys

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

with btrfs.FileSystem(sys.argv[1]) as fs:
    mixed_groups = fs.mixed_groups()
    usage = fs.usage()

    print("Mixed groups: {}".format(mixed_groups))
    print("Target profile for System (chunk tree): {}".format(usage.target_profile_system_str))
    if not mixed_groups:
        print("Target profile for Metadata: {}".format(usage.target_profile_metadata_str))
        print("Target profile for Data: {}".format(usage.target_profile_data_str))
    else:
        print("Target profile for Data+Metadata: {}".format(
            usage.target_profile_data_metadata_str))
    print()
    print("Virtual space usage by block group type:")
    print("|")
    virtual_block_group_type_usage_table_values = [
        ('type', 'total', 'used'),
        ('----', '-----', '----'),
    ]
    for _, virtual_block_group_type_usage in usage.virtual_block_group_type_usage.items():
        virtual_block_group_type_usage_table_values.append((
            btrfs.utils.space_type_description(virtual_block_group_type_usage.type),
            virtual_block_group_type_usage.total_str,
            virtual_block_group_type_usage.used_str,
        ))
    for virtual_block_group_type_usage_table_value in virtual_block_group_type_usage_table_values:
        print("| {: <16} {: >12} {: >12}".format(*virtual_block_group_type_usage_table_value))
    print()

    print("Total raw filesystem size: {}".format(usage.total_str))
    print("Total raw allocated bytes: {}".format(usage.allocated_str))
    print("Allocatable bytes remaining: {}".format(usage.allocatable_left_str))
    print("Unallocatable bytes that can be reclaimed by balancing: {}".format(
        usage.unallocatable_reclaimable_str))
    print("Unallocatable bytes because of unbalanced device sizes: {}".format(
        usage.unallocatable_hard_str))
    print()

    if not mixed_groups:
        print("Estimated virtual space left to use for metadata: {}".format(
            usage.free_metadata_str))
        print("Estimated virtual space left to use for data: {}".format(usage.free_data_str))
    else:
        print("Estimated virtual space left to use for metadata and data: {}".format(
            usage.free_str))
    print()

    print("Allocated raw disk bytes by chunk type. Parity is a reserved part of the \n"
          "allocated bytes, limiting the amount that can be used for data or metadata:")
    print("|")
    raw_space_usage_table_values = [
        ('flags', 'allocated', 'used', 'parity'),
        ('-----', '---------', '----', '------'),
    ]
    for _, raw_space_usage in usage.raw_space_usage.items():
        raw_space_usage_table_values.append((
            btrfs.utils.block_group_flags_str(raw_space_usage.flags),
            raw_space_usage.allocated_str,
            raw_space_usage.used_str,
            raw_space_usage.parity_str,
        ))
    for raw_space_usage_table_value in raw_space_usage_table_values:
        print("| {: <16} {: >12} {: >12} {: >12}".format(*raw_space_usage_table_value))
    print()

    print("Allocated bytes per device:")
    print("|")
    dev_usage_table_values = [
        ('devid', 'total size', 'allocated', 'path'),
        ('-----', '----------', '---------', '----'),
    ]
    for devid in sorted(usage.dev_usage.keys()):
        dev_usage = usage.dev_usage[devid]
        dev_usage_table_values.append((
            dev_usage.devid,
            dev_usage.total_str,
            dev_usage.allocated_str,
            btrfs.ioctl.dev_info(fs.fd, devid).path,
        ))
    for dev_usage_table_value in dev_usage_table_values:
        print("| {: <8} {: >12} {: >12} {}".format(*dev_usage_table_value))
    print()

    print("Allocated bytes per device, split up per chunk type. Parity bytes are again\n"
          "part of the total amount of allocated bytes.")
    for devid in sorted(usage.dev_usage.keys()):
        print("|")
        print("| Device ID: {}".format(devid))
        dev_usage = usage.dev_usage[devid]
        dev_space_usage_table_values = [
            ('flags', 'allocated', 'parity'),
            ('-----', '---------', '------'),
        ]
        for _, dev_space_usage in dev_usage.dev_space_usage.items():
            dev_space_usage_table_values.append((
                btrfs.utils.block_group_flags_str(dev_space_usage.flags),
                dev_space_usage.allocated_str,
                dev_space_usage.parity_str,
            ))
        for dev_space_usage_table_value in dev_space_usage_table_values:
            print("| | {: <16} {: >12} {: >12}".format(*dev_space_usage_table_value))
    print()

    print("Unallocatable bytes per device:")
    print("|")
    wasted_sizes_table_values = [
        ('devid', 'soft', 'hard', 'reclaimable'),
        ('-----', '----', '----', '-----------'),
    ]
    for devid in sorted(usage.dev_usage.keys()):
        dev_usage = usage.dev_usage[devid]
        wasted_sizes_table_values.append((
            devid,
            dev_usage.unallocatable_soft_str,
            dev_usage.unallocatable_hard_str,
            dev_usage.unallocatable_reclaimable_str,
        ))
    for wasted_sizes_table_value in wasted_sizes_table_values:
        print("| {: <8} {: >12} {: >12} {: >12}".format(*wasted_sizes_table_value))
