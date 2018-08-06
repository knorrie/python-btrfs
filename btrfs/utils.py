# Copyright (C) 2016-2017 Hans van Kranenburg <hans@knorrie.org>
#
# This file is part of the python-btrfs module.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License v2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

import btrfs
import collections.abc
import types
from btrfs.ctree import (
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_TYPE_MASK,
    BLOCK_GROUP_RAID0, BLOCK_GROUP_RAID1, BLOCK_GROUP_RAID5,
    BLOCK_GROUP_RAID6, BLOCK_GROUP_DUP, BLOCK_GROUP_RAID10,
    BLOCK_GROUP_SINGLE,
    BLOCK_GROUP_PROFILE_MASK,
)


def mounted_filesystems():
    filesystems = {}
    mounts = [line.split() for line in open('/proc/self/mounts', 'r').read().splitlines()]
    for path in [mount[1] for mount in mounts if mount[2] == 'btrfs']:
        fs = btrfs.ctree.FileSystem(path)
        filesystems.setdefault(fs.fsid, fs)
    return list(filesystems.values())


_space_type_description_map = {
    BLOCK_GROUP_DATA: 'Data',
    BLOCK_GROUP_SYSTEM: 'System',
    BLOCK_GROUP_METADATA: 'Metadata',
    BLOCK_GROUP_DATA | BLOCK_GROUP_METADATA: 'Data+Metadata',
    SPACE_INFO_GLOBAL_RSV: 'GlobalReserve',
}


def space_type_description(flags):
    return _space_type_description_map.get(
        flags & (BLOCK_GROUP_TYPE_MASK | SPACE_INFO_GLOBAL_RSV),
        'unknown'
    )


_space_profile_description_map = {
    BLOCK_GROUP_SINGLE: 'single',
    BLOCK_GROUP_RAID0: 'RAID0',
    BLOCK_GROUP_RAID1: 'RAID1',
    BLOCK_GROUP_RAID5: 'RAID5',
    BLOCK_GROUP_RAID6: 'RAID6',
    BLOCK_GROUP_DUP: 'DUP',
    BLOCK_GROUP_RAID10: 'RAID10',
}


def space_profile_description(flags):
    return _space_profile_description_map.get(
        flags & BLOCK_GROUP_PROFILE_MASK,
        'unknown'
    )


pretty_size_units = '_KMGTPE'


def pretty_size(size, unit=None, binary=True):
    if unit == '':
        return str(size)
    base = 1024 if binary else 1000
    if unit is None:
        if size == 0:
            unit = ''
            unit_offset = 0
            base = 1000
        else:
            unit_offset = 0
            tmp = size
            while tmp >= 1024 and unit_offset < len(pretty_size_units) - 1:
                unit_offset = unit_offset + 1
                tmp = tmp / 1024
            unit = pretty_size_units[unit_offset] if unit_offset > 0 else ''
    else:
        unit = unit.upper()
        unit_offset = pretty_size_units.index(unit)
        if unit == 'K' and base == 1000:
            unit = 'k'
    divide_by = base ** unit_offset
    if divide_by > 0:
        size = size / divide_by
    return "{0:.2f}{1}{2}B".format(size, unit, 'i' if base == 1024 and unit != '' else '')


def flags_str(flags, flags_str_map):
    ret = []
    for flag in sorted(flags_str_map.keys()):
        if flags & flag:
            ret.append(flags_str_map[flag])
            flags ^= flag
    if flags != 0:
        ret.append("unknown(0x{:0x})".format(flags))
    elif len(ret) == 0:
        ret.append("none")
    return '|'.join(ret)


def block_group_flags_str(flags):
    return flags_str(flags, btrfs.ctree._block_group_flags_str_map)


def block_group_type_str(flags):
    return block_group_flags_str(flags & BLOCK_GROUP_TYPE_MASK)


def block_group_profile_str(flags):
    return block_group_flags_str(flags & BLOCK_GROUP_PROFILE_MASK)


_block_group_profile_ratio_map = {
    BLOCK_GROUP_SINGLE: 1,
    BLOCK_GROUP_RAID0: 1,
    BLOCK_GROUP_RAID1: 2,
    BLOCK_GROUP_DUP: 2,
    BLOCK_GROUP_RAID10: 2,
    BLOCK_GROUP_RAID5: 0,
    BLOCK_GROUP_RAID6: 0,
    SPACE_INFO_GLOBAL_RSV: 0,
}


def block_group_profile_ratio(flags):
    return _block_group_profile_ratio_map.get(
        flags & BLOCK_GROUP_PROFILE_MASK
    )


def wasted_space_raid0_raid1(sizes, chunk_size=1024**3):
    while len(sizes) > 1:
        sizes = sorted(sizes)
        if sizes[-2] < chunk_size:
            sizes[-1] = sizes[-1] - sizes[-2]
            sizes[-2] = 0
        else:
            sizes[-1] = sizes[-1] - chunk_size
            sizes[-2] = sizes[-2] - chunk_size
        sizes = [size for size in sizes if size > 0]

    if len(sizes) == 0:
        return 0
    return sizes[0]


def fs_usage(fs):
    spaces = [space for space in fs.space_info()
              if space.type != btrfs.SPACE_INFO_GLOBAL_RSV]
    used = sum([space.raw_used_bytes for space in spaces])

    flags_raid0_data = (btrfs.BLOCK_GROUP_DATA | btrfs.BLOCK_GROUP_RAID0)
    flags_raid1_data = (btrfs.BLOCK_GROUP_DATA | btrfs.BLOCK_GROUP_RAID1)
    check_wasted = any([space.flags & flags_raid0_data == flags_raid0_data
                       or space.flags & flags_raid1_data == flags_raid1_data
                       for space in spaces])

    devices = list(fs.devices())

    if check_wasted:
        wasted_total = btrfs.utils.wasted_space_raid0_raid1(
            [device.total_bytes - device.bytes_used for device in devices])
        wasted_hard = btrfs.utils.wasted_space_raid0_raid1(
            [device.total_bytes for device in devices])
        wasted_soft = wasted_total - wasted_hard
    else:
        wasted_hard = wasted_soft = 0

    total = sum([device.total_bytes for device in devices])
    allocated = sum([device.bytes_used for device in devices])

    return total, allocated, used, wasted_hard, wasted_soft


def embedded_text_for_str(text):
    try:
        return "utf-8 {}".format(text.decode('utf-8'))
    except UnicodeDecodeError:
        return "raw {}".format(repr(text))


def _pretty_attr_value(obj, attr_name, stringify_fn=None):
    if stringify_fn is not None:
        return "{}: {}".format(attr_name, stringify_fn(getattr(obj, attr_name)))
    cls = obj.__class__
    attr_name_str = '_{}_str'.format(attr_name)
    stringify_property = getattr(cls, attr_name_str, None)
    if stringify_property is None:
        # try deprecated pattern
        attr_name_str = '{}_str'.format(attr_name)
        stringify_property = getattr(cls, attr_name_str, None)
    if stringify_property is not None and isinstance(stringify_property, property):
        return "{}: {}".format(attr_name, getattr(obj, attr_name_str))
    return "{}: {}".format(attr_name, getattr(obj, attr_name))


pretty_print_modules = 'btrfs.ctree', 'btrfs.ioctl', 'btrfs.fs_usage'


def pretty_obj_tuples(obj, level=0, seen=None):
    if seen is None:
        seen = []
    cls = obj.__class__
    if isinstance(obj, btrfs.ctree.ItemData) and \
            hasattr(obj, 'key') and isinstance(obj.key, btrfs.ctree.Key):
        yield level, "<{}.{} {}>".format(cls.__module__, cls.__name__, str(obj.key))
    elif cls.__module__ in pretty_print_modules:
        yield level, "<{}.{}>".format(cls.__module__, cls.__name__)
    if obj in seen:
        yield level, "[... object already seen, aborting recursion]"
        return
    seen.append(obj)
    if isinstance(obj, (list, types.GeneratorType)) or \
            (isinstance(obj, btrfs.ctree.ItemData) and
             isinstance(obj, collections.abc.MutableSequence)):
        for item in obj:
            yield level, '-'
            yield from pretty_obj_tuples(item, level+1, seen)
    elif cls.__module__ in pretty_print_modules and \
            not isinstance(obj, btrfs.ctree.Key):
        if isinstance(obj, btrfs.ctree.ItemData):
            objectid_attr, type_attr, offset_attr = obj.key_attrs
            if objectid_attr is not None:
                yield level, "{} (key objectid)".format(_pretty_attr_value(obj, objectid_attr))
            if type_attr is not None:
                yield level, "{} (key type)".format(_pretty_attr_value(obj, type_attr))
            if offset_attr is not None:
                yield level, "{} (key offset)".format(_pretty_attr_value(obj, offset_attr))
        for attr_name, attr_value in obj.__dict__.items():
            if attr_name.startswith('_'):
                continue
            if isinstance(obj, btrfs.ctree.ItemData):
                if attr_name in obj.key_attrs:
                    continue
                if attr_name == 'key' and isinstance(attr_value, btrfs.ctree.Key):
                    continue
            if isinstance(attr_value, list):
                if len(attr_value) == 0:
                    continue
                yield level, "{}:".format(attr_name)
                for item in attr_value:
                    yield level, '-'
                    yield from pretty_obj_tuples(item, level+1, seen)
            elif isinstance(attr_value, dict):
                if len(attr_value) == 0:
                    continue
                yield level, "{}:".format(attr_name)
                for k, v in attr_value.items():
                    dict_key_str = '_{}_key_str'.format(attr_name)
                    stringify_fn = getattr(cls, dict_key_str, None)
                    if stringify_fn is None:
                        # try deprecated pattern
                        dict_key_str = '{}_key_str'.format(attr_name)
                        stringify_fn = getattr(cls, dict_key_str, None)
                    if stringify_fn is not None and callable(stringify_fn):
                        yield level+1, "{}:".format(stringify_fn(k))
                    else:
                        yield level+1, "{}:".format(k)
                    yield from pretty_obj_tuples(v, level+2, seen)
            elif attr_value.__class__.__module__ in pretty_print_modules and \
                    not isinstance(attr_value, (btrfs.ctree.Key, btrfs.ctree.TimeSpec)):
                yield level, "{}:".format(attr_name)
                yield from pretty_obj_tuples(attr_value, level+1, seen)
            else:
                yield level, _pretty_attr_value(obj, attr_name)
    else:
        yield level, str(obj)
    seen.pop()


def pretty_obj_lines(obj, level=0):
    for level, line in pretty_obj_tuples(obj, level):
        yield "{}{}".format('  ' * level, line)


def pretty_print(obj, level=0):
    for line in pretty_obj_lines(obj, level):
        print(line)
