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

SZ_1K = 0x00000400
SZ_2K = 0x00000800
SZ_4K = 0x00001000
SZ_8K = 0x00002000
SZ_16K = 0x00004000
SZ_32K = 0x00008000
SZ_64K = 0x00010000
SZ_128K = 0x00020000
SZ_256K = 0x00040000
SZ_512K = 0x00080000

SZ_1M = 0x00100000
SZ_2M = 0x00200000
SZ_4M = 0x00400000
SZ_8M = 0x00800000
SZ_16M = 0x01000000
SZ_32M = 0x02000000
SZ_64M = 0x04000000
SZ_128M = 0x08000000
SZ_256M = 0x10000000
SZ_512M = 0x20000000

SZ_1G = 0x40000000


def mounted_filesystem_paths():
    filesystems = {}
    mounts = [line.split() for line in open('/proc/self/mounts', 'r').read().splitlines()]
    for path in [mount[1] for mount in mounts if mount[2] == 'btrfs']:
        with btrfs.ctree.FileSystem(path) as fs:
            filesystems.setdefault(fs.fsid, path)
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
