# Copyright (C) 2016 Hans van Kranenburg <hans@knorrie.org>
#
# This file is part of the python-btrfs module.
#
# python-btrfs is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-btrfs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with python-btrfs.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains miscellanious collection of things, like the
:func:`pretty_print` function which provides a quick readable textual dump of
most of the object types in this library. Besides that, some functions to
pretty print and parse size strings and some other stuff.
"""

import btrfs
import collections.abc
import re
import types
from btrfs.ctree import (
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_TYPE_MASK,
    BLOCK_GROUP_RAID0, BLOCK_GROUP_RAID1, BLOCK_GROUP_RAID5,
    BLOCK_GROUP_RAID1C3, BLOCK_GROUP_RAID1C4,
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
    """Discover mountpoints for online btrfs filesystems

    :returns: Filesystem paths where btrfs filesystems are mounted.
    :rtype: List[str]
    """
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
    """
    :param int flags: Space flags.
    :returns: String representation of the space type only.
    :rtype: str

    Example::

        >>> btrfs.utils.space_type_description(0x14)
        'Metadata'
    """
    return _space_type_description_map.get(
        flags & (BLOCK_GROUP_TYPE_MASK | SPACE_INFO_GLOBAL_RSV),
        'unknown'
    )


_space_profile_description_map = {
    BLOCK_GROUP_SINGLE: 'single',
    BLOCK_GROUP_RAID0: 'RAID0',
    BLOCK_GROUP_RAID1: 'RAID1',
    BLOCK_GROUP_RAID1C3: 'RAID1C3',
    BLOCK_GROUP_RAID1C4: 'RAID1C4',
    BLOCK_GROUP_RAID5: 'RAID5',
    BLOCK_GROUP_RAID6: 'RAID6',
    BLOCK_GROUP_DUP: 'DUP',
    BLOCK_GROUP_RAID10: 'RAID10',
}


def space_profile_description(flags):
    """
    :param int flags: Space flags.
    :returns: String representation of the space profile only.
    :rtype: str

    Example::

        >>> btrfs.utils.space_profile_description(0x14)
        'RAID1'
    """
    return _space_profile_description_map.get(
        flags & BLOCK_GROUP_PROFILE_MASK,
        'unknown'
    )


def space_flags_description(flags):
    """
    :param int flags: Space flags.
    :returns: String representation of the space type and profile.
    :rtype: str

    Example::

        >>> btrfs.utils.space_flags_description(0x14)
        'Metadata, RAID1'
    """
    return "{}, {}".format(
        btrfs.utils.space_type_description(flags),
        btrfs.utils.space_profile_description(flags))


pretty_size_units = '_KMGTPE'


def pretty_size(size, unit=None, binary=True):
    """
    :param int size: Size in bytes.
    :param str unit: Target unit to display the size in. One of 'kMGTPE'.
    :param bool binary: If True, use base 1024, else base 1000.

    Example::

        >>> btrfs.utils.pretty_size(1610612736, unit='G')
        '1.50GiB'
    """
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


_re_parse_pretty_size = re.compile(r'^(?P<size>\d+)(?:(?P<unit>[kMGTPE])((?P<i>i)?B)?)?$')


def parse_pretty_size(size_str):
    """Parse pretty printed size strings.

    This is the opposite of the :func:`pretty_size` function, but not 100%.

    :param str size_str: String literal to be parsed.
    :raises ValueError: If the input cannot be parsed as pretty size.

    Example::

            >>> btrfs.utils.parse_pretty_size('234MB')
            234000000
            >>> btrfs.utils.parse_pretty_size('234MiB')
            245366784
            >>> btrfs.utils.parse_pretty_size('234TB')
            234000000000000
            >>> btrfs.utils.parse_pretty_size('234TiB')
            257285720899584
            >>> btrfs.utils.parse_pretty_size('1048576')
            1048576
    """
    match = _re_parse_pretty_size.match(size_str)
    if match is None:
        raise ValueError('literal cannot be parsed as pretty size')
    groupdict = match.groupdict()
    if groupdict['unit'] is None:
        return int(size_str)
    base = 1024 if groupdict['i'] == 'i' else 1000
    unit_offset = pretty_size_units.index(groupdict['unit'].upper())
    multiply_by = base ** unit_offset
    return int(groupdict['size']) * multiply_by


def flags_str(flags, flags_str_map):
    """Generic helper to convert flags to a description.

    This function is used by more specific helper functions below. You probably
    don't need to call it directly.

    :param int flags: Flags.
    :param flags_str_map: Mapping from flag bit value to description.
    :type flags_str_map: dict(int, str)
    """
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
    """
    :param int flags: Block Group flags.
    :returns: String representation of the block group type and profile.
    :rtype: str

    Example::

        >>> btrfs.utils.block_group_flags_str(0x14)
        'METADATA|RAID1'
    """
    return flags_str(flags, btrfs.ctree._block_group_flags_str_map)


def block_group_type_str(flags):
    """
    :param int flags: Block Group flags.
    :returns: String representation of the block group type only.
    :rtype: str

    Example::

        >>> btrfs.utils.block_group_type_str(0x14)
        'METADATA'
    """
    return block_group_flags_str(flags & BLOCK_GROUP_TYPE_MASK)


def block_group_profile_str(flags):
    """
    :param int flags: Block Group flags.
    :returns: String representation of the block group profile only.
    :rtype: str

    Example::

        >>> btrfs.utils.block_group_profile_str(0x14)
        'RAID1'
    """
    return block_group_flags_str(flags & BLOCK_GROUP_PROFILE_MASK)


def extent_flags_str(flags):
    """
    :param int flags: :class:`~btrfs.ctree.ExtentItem` flags.
    :returns: String representation of the extent item flags.
    :rtype: str

    Example::

        >>> btrfs.utils.extent_flags_str(0x102)
        'TREE_BLOCK|FULL_BACKREF'
    """
    return flags_str(flags, btrfs.ctree._extent_flags_str_map)


def inode_mode_str(mode):
    """
    :param int mode: File mode as number.
    :returns: String representation of file mode in octal format.
    :rtype: str

    Example::

        >>> btrfs.utils.inode_mode_str(16877)
        '040755'

    """
    return "0{:05o}".format(mode)


def inode_flags_str(flags):
    """
    :param int flags: :class:`~btrfs.ctree.InodeItem` flags.
    :returns: String representation of the inode item flags.
    :rytpe: str

    Example::

        >>> btrfs.utils.inode_flags_str(72)
        'NOCOMPRESS|IMMUTABLE'
    """
    return flags_str(flags, btrfs.ctree._inode_flags_str_map)


def dir_item_type_str(type_):
    """
    :param int type_: :class:`~btrfs.ctree.DirItem` type.
    :returns: String representation of DirItem type.
    :rtype: str

    Example::

        >>> btrfs.utils.dir_item_type_str(4)
        'BLKDEV'
    """
    return btrfs.ctree._dir_item_type_str_map[type_]


def root_item_flags_str(flags):
    """
    :param int flags: :class:`~btrfs.ctree.RootItem` flags.
    :returns: String representation of RootItem flags.
    :rtype: str

    Example::

        >>> btrfs.utils.root_item_flags_str(1)
        'RDONLY'
    """
    return flags_str(flags, btrfs.ctree._root_flags_str_map)


def compress_type_str(compression):
    """
    :param int compression: :class:`~btrfs.ctree.FileExtentItem` compression
        type.
    :returns: String representation of compression type.
    :rtype: str

    Example::

        >>> btrfs.utils.compress_type_str(3)
        'zstd'
    """
    return btrfs.ctree._compress_type_str_map.get(compression, 'unknown')


def file_extent_type_str(type_):
    """
    :param int type_: :class:`~btrfs.ctree.FileExtentItem` type.
    :returns: String representation of FileExtentItem type.
    :rtype: str

    Example::

        >>> btrfs.utils.file_extent_type_str(0)
        'inline'
    """
    return btrfs.ctree._file_extent_type_str_map.get(type_, 'unknown')


def free_space_info_flags_str(flags):
    """
    :param int flags: :class:`~btrfs.ctree.FreeSpaceInfo` flags.
    :returns: String representation of FreeSpaceInfo flags.
    :rtype: str

    Example::

        >>> btrfs.utils.free_space_info_flags_str(1)
        'bitmaps'
    """
    return flags_str(flags, btrfs.ctree._free_space_info_flags_str_map)


def embedded_text_for_str(text):
    """
    :param bytes text: bytes from a name of data field of an object from the
        :class:`btrfs.ctree.DirItem` family.
    :returns: String representation of the bytes.
    :rtype: str

    This function is not intended to be used for anything else than a
    convienient way of displaying filenames and xattr keys and values in the
    pretty printer.

    Example::

        >>> name_bytes = b'\\xce\\xbc\\xce\\xbf\\xcf\\x85\\xcf\\x84\\xce\\xbf\\xce\\xbd'
        >>> btrfs.utils.embedded_text_for_str(name_bytes)
        "utf-8 'μουτον'"
    """
    if len(text) == 0:
        return "<empty>"
    try:
        return "utf-8 '{}'".format(text.decode('utf-8'))
    except UnicodeDecodeError:
        return "raw '{}'".format(repr(text))


_tree_name_id_map = {
    'root': btrfs.ctree.ROOT_TREE_OBJECTID,
    'extent': btrfs.ctree.EXTENT_TREE_OBJECTID,
    'chunk': btrfs.ctree.CHUNK_TREE_OBJECTID,
    'dev': btrfs.ctree.DEV_TREE_OBJECTID,
    'fs': btrfs.ctree.FS_TREE_OBJECTID,
    'csum': btrfs.ctree.CSUM_TREE_OBJECTID,
    'quota': btrfs.ctree.QUOTA_TREE_OBJECTID,
    'uuid': btrfs.ctree.UUID_TREE_OBJECTID,
    'free_space': btrfs.ctree.FREE_SPACE_TREE_OBJECTID,
    'tree_log': btrfs.ctree.TREE_LOG_OBJECTID,
    'tree_log_fixup': btrfs.ctree.TREE_LOG_FIXUP_OBJECTID,
    'tree_reloc': btrfs.ctree.TREE_RELOC_OBJECTID,
    'data_reloc': btrfs.ctree.DATA_RELOC_TREE_OBJECTID,
}


def parse_tree_name(name):
    """Convert a tree name to an actual root tree objectid number

    :param string name: tree name with optional _tree suffix or number
        formatted as string
    :returns: Tree objectid that is valid for the root tree
    :rtype: int

    Example::

        >>> btrfs.utils.parse_tree_name('EXTENT_TREE')
        2
        >>> btrfs.utils.parse_tree_name('extent_tree')
        2
        >>> btrfs.utils.parse_tree_name('extent')
        2
        >>> btrfs.utils.parse_tree_name('2')
        2
        >>> btrfs.utils.parse_tree_name(2)
        2
    """
    try:
        return int(name)
    except ValueError:
        pass
    lower_name = name.lower()
    if lower_name[-5:] == '_tree':
        lookup_name = lower_name[:-5]
    else:
        lookup_name = lower_name
    if lookup_name in _tree_name_id_map:
        return _tree_name_id_map[lookup_name]
    raise ValueError("Unknown metadata tree name " + name)


def parse_key_string(key_str):
    """Create a Key object from a pretty printed string representation

    :param string key_str: String representation of a key, e.g. '(31832 INODE_REF 31798)'
    :returns: A Key object with the parsed values set
    :rtype: :class:`~btrfs.ctree.Key`
    :raises: :class:`ValueError` if the key string is an invalid key representation

    The parentheses around the key triplet are optional.

    Example::

        >>> btrfs.utils.parse_key_string('(31832 INODE_REF 31798)')
        Key(31832, 12, 31798)
        >>> btrfs.utils.parse_key_string('(535 EXTENT_DATA 0)')
        Key(535, 108, 0)

    """
    if key_str[0] == '(' and key_str[-1] == ')':
        key_str = key_str[1:-1]
    try:
        objectid_str, type_str, offset_str = key_str.split()
    except ValueError:
        raise ValueError(
            "Key representation needs 3 fields: objectid, type, offset: {}".format(key_str)) \
            from None
    return btrfs.ctree.Key(objectid_str, type_str, offset_str)


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
    value = getattr(obj, attr_name)
    if isinstance(value, (memoryview, bytes)):
        return "{}: {} bytes of data".format(attr_name, len(value))
    return "{}: {}".format(attr_name, value)


pretty_print_modules = 'btrfs.ctree', 'btrfs.ioctl', 'btrfs.fs_usage', 'btrfs.free_space_tree'


def _pretty_obj_tuples(obj, level=0, seen=None):
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
    known = False
    if cls.__module__ in pretty_print_modules and \
            not isinstance(obj, btrfs.ctree.Key):
        known = True
        if isinstance(obj, btrfs.ctree.ItemData):
            try:
                objectid_attr, type_attr, offset_attr = obj._key_attrs
                if objectid_attr is not None:
                    yield level, "{} (key objectid)".format(_pretty_attr_value(obj, objectid_attr))
                if type_attr is not None:
                    yield level, "{} (key type)".format(_pretty_attr_value(obj, type_attr))
                if offset_attr is not None:
                    yield level, "{} (key offset)".format(_pretty_attr_value(obj, offset_attr))
            except AttributeError:
                pass
        for attr_name, attr_value in obj.__dict__.items():
            if attr_name.startswith('_'):
                continue
            if isinstance(obj, btrfs.ctree.ItemData):
                try:
                    if attr_name in obj._key_attrs:
                        continue
                except AttributeError:
                    pass
                if attr_name == 'key' and isinstance(attr_value, btrfs.ctree.Key):
                    continue
            if isinstance(attr_value, list):
                if len(attr_value) == 0:
                    continue
                yield level, "{}:".format(attr_name)
                for item in attr_value:
                    yield level, '-'
                    yield from _pretty_obj_tuples(item, level+1, seen)
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
                    yield from _pretty_obj_tuples(v, level+2, seen)
            elif attr_value.__class__.__module__ in pretty_print_modules and \
                    not isinstance(attr_value, (btrfs.ctree.Key, btrfs.ctree.TimeSpec)):
                yield level, "{}:".format(attr_name)
                yield from _pretty_obj_tuples(attr_value, level+1, seen)
            else:
                yield level, _pretty_attr_value(obj, attr_name)
    if isinstance(obj, (list, types.GeneratorType)) or \
            (isinstance(obj, btrfs.ctree.ItemData) and
             isinstance(obj, collections.abc.MutableSequence)):
        known = True
        for item in obj:
            yield level, '-'
            yield from _pretty_obj_tuples(item, level+1, seen)
    elif isinstance(obj, dict) and len(obj) != 0:
        known = True
        for k, v in obj.items():
            yield level, "{}:".format(k)
            yield from _pretty_obj_tuples(v, level+1, seen)
    if not known:
        yield level, str(obj)
    seen.pop()


def _pretty_obj_lines(obj, level=0):
    for level, line in _pretty_obj_tuples(obj, level):
        yield "{}{}".format('  ' * level, line)


def _pretty_print(obj, level=0):
    for line in _pretty_obj_lines(obj, level):
        print(line)


def pretty_print(obj):
    """
    The pretty printer dumps content of objects on the screen. It is mainly
    designed to work with objects from the btrfs library. It is also possible
    to provide a lists of objects, or a generator, or even nested structures.

    :param obj: An object to pretty print, or a collection of them.
    :type obj: anything goes

    Example::

        >>> import btrfs
        >>> with btrfs.FileSystem('/') as fs:
        ...     btrfs.utils.pretty_print(fs.block_group(1687427219456))
        ...
        <btrfs.ctree.BlockGroupItem (1687427219456 BLOCK_GROUP_ITEM 1073741824)>
        vaddr: 1687427219456 (key objectid)
        length: 1.00GiB (key offset)
        flags: DATA
        chunk_objectid: 256
        used: 960.50MiB
    """
    _pretty_print(obj)


def _str_obj_tuples(obj, level=0, seen=None):
    if seen is None:
        seen = []
    cls = obj.__class__
    if cls.__module__ in pretty_print_modules and \
            not isinstance(obj, (btrfs.ctree.Key, btrfs.ctree.TimeSpec)):
        yield level, str(obj)
    if obj in seen:
        yield level, "[... object already seen, aborting recursion]"
        return
    seen.append(obj)
    if isinstance(obj, btrfs.ctree.ItemData):
        for attr_name, attr_value in obj.__dict__.items():
            if attr_name.startswith('_'):
                continue
            if isinstance(obj, (btrfs.ctree.ItemData, btrfs.ctree.SubItem)):
                yield from _str_obj_tuples(attr_value, level+1, seen)
            elif isinstance(attr_value, list):
                for item in attr_value:
                    yield from _str_obj_tuples(item, level+1, seen)
    if isinstance(obj, (list, types.GeneratorType)):
        for item in obj:
            yield from _str_obj_tuples(item, level, seen)
    elif isinstance(obj, btrfs.ctree.ItemData) and \
            isinstance(obj, collections.abc.MutableSequence):
        for item in obj:
            yield from _str_obj_tuples(item, level+1, seen)
    seen.pop()


def _str_print_lines(obj, level=0):
    for level, line in _str_obj_tuples(obj, level):
        yield "{}{}".format('  ' * level, line)


def str_print(obj):
    """
    Print the usual str() of an object, but look inside to see if more ItemData
    objects are hidden there. If so, also print their str().

    :param obj: An object to pretty print, or a collection of them.
    :type obj: anything goes

    Example::

        >>> with btrfs.FileSystem('/') as fs:
        ...      btrfs.utils.str_print(fs.block_group(63381176320))
        ...
        block group vaddr 63381176320 length 1073741824 flags DATA used 1073741824 used_pct 100
    """
    for line in _str_print_lines(obj):
        print(line)
