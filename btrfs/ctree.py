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
This module contains Python object representations for btrfs metadata items.

Additionally, the helper :class:`FileSystem` provides a convenient way to start
exploring an online btrfs filesystem.
"""

import btrfs
import collections.abc
import copy
import datetime
import os
import re
import struct
import uuid

U8_MAX = (1 << 8) - 1
ULLONG_MAX = (1 << 64) - 1
ULONG_MAX = (1 << 32) - 1


def U8(n):
    """
    :param int n: Any number.
    :returns: Unsigned 8 bit number.
    :rtype: int

    Example::

        >>> btrfs.ctree.U8(64)
        64
        >>> btrfs.ctree.U8(-1)
        255
        >>> btrfs.ctree.U8(0x4000)
        0

    """
    return n & U8_MAX


def ULL(n):
    """
    :param int n: Any number.
    :returns: Unsigned 64 bit number.
    :rtype: int

    Example::

        >>> btrfs.ctree.ULL(64)
        64
        >>> btrfs.ctree.ULL(-1)
        18446744073709551615
        >>> btrfs.ctree.ULL(0x4000)
        16384
    """
    return n & ULLONG_MAX


def _struct_format(s):
    f = s.format
    # Python <= 3.6 returns bytes, 3.7 returns str, yay.
    if type(f) == bytes:
        return f.decode('utf-8')
    return f


ROOT_TREE_OBJECTID = 1  #: Root tree
EXTENT_TREE_OBJECTID = 2  #: Extent tree
CHUNK_TREE_OBJECTID = 3  #: Chunk tree
DEV_TREE_OBJECTID = 4  #: Device tree
FS_TREE_OBJECTID = 5  #: Top level subvolume tree
ROOT_TREE_DIR_OBJECTID = 6  #: Used in the root tree to store default subvolume information.
CSUM_TREE_OBJECTID = 7  #: Checksum tree
QUOTA_TREE_OBJECTID = 8  #: Quota tree
UUID_TREE_OBJECTID = 9  #: Subvolume UUID tree
FREE_SPACE_TREE_OBJECTID = 10  #: Free space tree

DEV_STATS_OBJECTID = 0  #: Object ID of device statistics in the Device tree.
BALANCE_OBJECTID = ULL(-4)  #: Object ID to store balance status. (-4)
ORPHAN_OBJECTID = ULL(-5)  #: Object ID to store orphans that need cleaning. (-5)
TREE_LOG_OBJECTID = ULL(-6)
TREE_LOG_FIXUP_OBJECTID = ULL(-7)
TREE_RELOC_OBJECTID = ULL(-8)
DATA_RELOC_TREE_OBJECTID = ULL(-9)
EXTENT_CSUM_OBJECTID = ULL(-10)  #: Object ID used for checksum items. (-10)
FREE_SPACE_OBJECTID = ULL(-11)  #: Object ID for free space cache v1 items. (-11)
FREE_INO_OBJECTID = ULL(-12)
MULTIPLE_OBJECTIDS = ULL(-255)

FIRST_FREE_OBJECTID = 256  #: First available Object ID for subvolume trees.
LAST_FREE_OBJECTID = ULL(-256)  #: Last available Object ID for subvolume trees. (-256)
FIRST_CHUNK_TREE_OBJECTID = 256  #: Object ID for Chunk objects in the Chunk tree.

DEV_ITEMS_OBJECTID = 1  #: Object ID for Device items in the Device tree.


INODE_ITEM_KEY = 1  #: Key type used by :class:`InodeItem`
INODE_REF_KEY = 12  #: Key type used by :class:`InodeRefList`
INODE_EXTREF_KEY = 13  # Key type used by :class:`InodeExtrefList(`
XATTR_ITEM_KEY = 24  #: Key type used by :class:`XAttrItemList`
ORPHAN_ITEM_KEY = 48  #: Key type used to track orphaned roots.
DIR_LOG_ITEM_KEY = 60
DIR_LOG_INDEX_KEY = 72
DIR_ITEM_KEY = 84  #: Key type used by :class:`DirItemList`
DIR_INDEX_KEY = 96  #: Key type used by :class:`DirIndex`
EXTENT_DATA_KEY = 108  #: Key type used by :class:`FileExtentItem`
EXTENT_CSUM_KEY = 128  #: Key type used for checksum items.
ROOT_ITEM_KEY = 132  #: Key type used by :class:`RootItem`
ROOT_BACKREF_KEY = 144
ROOT_REF_KEY = 156  #: Key type used by :class:`RootRef`
EXTENT_ITEM_KEY = 168  #: Key type used by :class:`ExtentItem`
METADATA_ITEM_KEY = 169  #: Key type used by :class:`MetaDataItem`
TREE_BLOCK_REF_KEY = 176  #: Key type used by :class:`TreeBlockRef`
EXTENT_DATA_REF_KEY = 178  #: Key type used by :class:`ExtentDataRef`
SHARED_BLOCK_REF_KEY = 182  #: Key type used by :class:`SharedBlockRef`
SHARED_DATA_REF_KEY = 184  #: Key type used by :class:`SharedDataRef`
BLOCK_GROUP_ITEM_KEY = 192  #: Key type used by :class:`BlockGroupItem`
FREE_SPACE_INFO_KEY = 198  #: Key type used by :class:`FreeSpaceInfo`
FREE_SPACE_EXTENT_KEY = 199  #: Key type used by :class:`FreeSpaceExtent`
FREE_SPACE_BITMAP_KEY = 200  #: Key type used by :class:`FreeSpaceBitmap`
DEV_EXTENT_KEY = 204  #: Key type used by :class:`DevExtent`
DEV_ITEM_KEY = 216  #: Key type used by :class:`DevItem`
CHUNK_ITEM_KEY = 228  #: Key type used by :class:`Chunk`
QGROUP_STATUS_KEY = 240
QGROUP_INFO_KEY = 242
QGROUP_LIMIT_KEY = 244
QGROUP_RELATION_KEY = 246
BALANCE_ITEM_KEY = 248  #: Balance status item key. Replaced by `TEMPORARY_ITEM_KEY`.
TEMPORARY_ITEM_KEY = 248  #: Key for various short term persistent stored items.
DEV_STATS_KEY = 249  #: Device statistics key. Replaced by `PERSISTENT_ITEM_KEY`.
PERSISTENT_ITEM_KEY = 249  #: Key for various long term persistent stored items.
DEV_REPLACE_KEY = 250
UUID_KEY_SUBVOL = 251
UUID_KEY_RECEIVED_SUBVOL = 252
STRING_ITEM_KEY = 253

BLOCK_GROUP_SINGLE = 0  #: Block Group single type. Does not exist in kernel code.
BLOCK_GROUP_DATA = 1 << 0  #: Block Group DATA type.
BLOCK_GROUP_SYSTEM = 1 << 1  #: Block Group SYSTEM type.
BLOCK_GROUP_METADATA = 1 << 2  #: Block Group METADATA type.
BLOCK_GROUP_RAID0 = 1 << 3  #: Block Group RAID0 profile.
BLOCK_GROUP_RAID1 = 1 << 4  #: Block Group RAID1 profile.
BLOCK_GROUP_DUP = 1 << 5  #: Block Group DUP profile.
BLOCK_GROUP_RAID10 = 1 << 6  #: Block Group RAID10 profile.
BLOCK_GROUP_RAID5 = 1 << 7  #: Block Group RAID5 profile.
BLOCK_GROUP_RAID6 = 1 << 8  #: Block Group RAID6 profile.
BLOCK_GROUP_RAID1C3 = 1 << 9  #: Block Group RAID1C3 profile.
BLOCK_GROUP_RAID1C4 = 1 << 10  #: Block Group RAID1C4 profile.

BLOCK_GROUP_TYPE_MASK = (
    BLOCK_GROUP_DATA |
    BLOCK_GROUP_SYSTEM |
    BLOCK_GROUP_METADATA
)  #: All Block Group type bits (data, system, metadata).

BLOCK_GROUP_PROFILE_MASK = (
    BLOCK_GROUP_RAID0 |
    BLOCK_GROUP_RAID1 |
    BLOCK_GROUP_RAID1C3 |
    BLOCK_GROUP_RAID1C4 |
    BLOCK_GROUP_RAID5 |
    BLOCK_GROUP_RAID6 |
    BLOCK_GROUP_DUP |
    BLOCK_GROUP_RAID10
)  #: All Block Group profile bits (raid1, dup, etc...).

AVAIL_ALLOC_BIT_SINGLE = 1 << 48  # used in balance_args
SPACE_INFO_GLOBAL_RSV = 1 << 49


_block_group_flags_str_map = {
    BLOCK_GROUP_DATA: 'DATA',
    BLOCK_GROUP_METADATA: 'METADATA',
    BLOCK_GROUP_SYSTEM: 'SYSTEM',
    BLOCK_GROUP_RAID0: 'RAID0',
    BLOCK_GROUP_RAID1: 'RAID1',
    BLOCK_GROUP_DUP: 'DUP',
    BLOCK_GROUP_RAID10: 'RAID10',
    BLOCK_GROUP_RAID5: 'RAID5',
    BLOCK_GROUP_RAID6: 'RAID6',
    BLOCK_GROUP_RAID1C3: 'RAID1C3',
    BLOCK_GROUP_RAID1C4: 'RAID1C4',
}

_balance_args_profiles_str_map = {
    BLOCK_GROUP_RAID0: 'RAID0',
    BLOCK_GROUP_RAID1: 'RAID1',
    BLOCK_GROUP_DUP: 'DUP',
    BLOCK_GROUP_RAID10: 'RAID10',
    BLOCK_GROUP_RAID5: 'RAID5',
    BLOCK_GROUP_RAID6: 'RAID6',
    BLOCK_GROUP_RAID1C3: 'RAID1C3',
    BLOCK_GROUP_RAID1C4: 'RAID1C4',
    AVAIL_ALLOC_BIT_SINGLE: 'SINGLE',
}

QGROUP_LEVEL_SHIFT = 48

EXTENT_FLAG_DATA = 1 << 0
EXTENT_FLAG_TREE_BLOCK = 1 << 1
BLOCK_FLAG_FULL_BACKREF = 1 << 8

_extent_flags_str_map = {
    EXTENT_FLAG_DATA: 'DATA',
    EXTENT_FLAG_TREE_BLOCK: 'TREE_BLOCK',
    BLOCK_FLAG_FULL_BACKREF: 'FULL_BACKREF',
}

INODE_NODATASUM = 1 << 0
INODE_NODATACOW = 1 << 1
INODE_READONLY = 1 << 2
INODE_NOCOMPRESS = 1 << 3
INODE_PREALLOC = 1 << 4
INODE_SYNC = 1 << 5
INODE_IMMUTABLE = 1 << 6
INODE_APPEND = 1 << 7
INODE_NODUMP = 1 << 8
INODE_NOATIME = 1 << 9
INODE_DIRSYNC = 1 << 10
INODE_COMPRESS = 1 << 11
INODE_ROOT_ITEM_INIT = 1 << 31

_inode_flags_str_map = {
    INODE_NODATASUM: 'NODATASUM',
    INODE_NODATACOW: 'NODATACOW',
    INODE_READONLY: 'READONLY',
    INODE_NOCOMPRESS: 'NOCOMPRESS',
    INODE_PREALLOC: 'PREALLOC',
    INODE_SYNC: 'SYNC',
    INODE_IMMUTABLE: 'IMMUTABLE',
    INODE_APPEND: 'APPEND',
    INODE_NODUMP: 'NODUMP',
    INODE_NOATIME: 'NOATIME',
    INODE_DIRSYNC: 'DIRSYNC',
    INODE_COMPRESS: 'COMPRESS',
    INODE_ROOT_ITEM_INIT: 'ROOT_ITEM_INIT',
}

ROOT_SUBVOL_RDONLY = 1 << 0

_root_flags_str_map = {
    ROOT_SUBVOL_RDONLY: 'RDONLY',
}

FT_UNKNOWN = 0
FT_REG_FILE = 1
FT_DIR = 2
FT_CHRDEV = 3
FT_BLKDEV = 4
FT_FIFO = 5
FT_SOCK = 6
FT_SYMLINK = 7
FT_XATTR = 8
FT_MAX = 9

_dir_item_type_str_map = {
    FT_UNKNOWN: 'UNKNOWN',
    FT_REG_FILE: 'FILE',
    FT_DIR: 'DIR',
    FT_CHRDEV: 'CHRDEV',
    FT_BLKDEV: 'BLKDEV',
    FT_FIFO: 'FIFO',
    FT_SOCK: 'SOCK',
    FT_SYMLINK: 'SYMLINK',
    FT_XATTR: 'XATTR',
}

COMPRESS_NONE = 0
COMPRESS_ZLIB = 1
COMPRESS_LZO = 2
COMPRESS_ZSTD = 3

_compress_type_str_map = {
    COMPRESS_NONE: 'none',
    COMPRESS_ZLIB: 'zlib',
    COMPRESS_LZO: 'lzo',
    COMPRESS_ZSTD: 'zstd',
}

FILE_EXTENT_INLINE = 0
FILE_EXTENT_REG = 1
FILE_EXTENT_PREALLOC = 2

_file_extent_type_str_map = {
    FILE_EXTENT_INLINE: 'inline',
    FILE_EXTENT_REG: 'regular',
    FILE_EXTENT_PREALLOC: 'prealloc',
}

FREE_SPACE_USING_BITMAPS = 1

_free_space_info_flags_str_map = {
    FREE_SPACE_USING_BITMAPS: 'bitmaps',
}


def qgroup_level(objectid):
    """Helper to get qgroup level from a qgroup relation objectid.

    :param int objectid: 64-bit object ID field.
    :returns: qgroup level.
    :rtype: int
    """
    return objectid >> QGROUP_LEVEL_SHIFT


def qgroup_subvid(objectid):
    """Helper to get qgroup subvolume ID from a qgroup relation objectid.

    :param int objectid: 64-bit object ID field.
    :returns: qgroup subvolume ID.
    :rtype: int
    """
    return objectid & ((1 << QGROUP_LEVEL_SHIFT) - 1)


def _qgroup_objectid(level, subvid):
    return (level << QGROUP_LEVEL_SHIFT) + subvid


_key_objectid_str_map = {
    ROOT_TREE_OBJECTID: 'ROOT_TREE',
    EXTENT_TREE_OBJECTID: 'EXTENT_TREE',
    CHUNK_TREE_OBJECTID: 'CHUNK_TREE',
    DEV_TREE_OBJECTID: 'DEV_TREE',
    FS_TREE_OBJECTID: 'FS_TREE',
    ROOT_TREE_DIR_OBJECTID: 'ROOT_TREE_DIR',
    CSUM_TREE_OBJECTID: 'CSUM_TREE',
    QUOTA_TREE_OBJECTID: 'QUOTA_TREE',
    UUID_TREE_OBJECTID: 'UUID_TREE',
    FREE_SPACE_TREE_OBJECTID: 'FREE_SPACE_TREE',
    BALANCE_OBJECTID: 'BALANCE',
    ORPHAN_OBJECTID: 'ORPHAN',
    TREE_LOG_OBJECTID: 'TREE_LOG',
    TREE_LOG_FIXUP_OBJECTID: 'TREE_LOG_FIXUP',
    TREE_RELOC_OBJECTID: 'TREE_RELOC',
    DATA_RELOC_TREE_OBJECTID: 'DATA_RELOC_TREE',
    EXTENT_CSUM_OBJECTID: 'EXTENT_CSUM',
    FREE_SPACE_OBJECTID: 'FREE_SPACE',
    FREE_INO_OBJECTID: 'FREE_INO',
    MULTIPLE_OBJECTIDS: 'MULTIPLE',
}


def _key_objectid_str(objectid, _type):
    if _type == DEV_EXTENT_KEY:
        return str(objectid)
    if _type == QGROUP_RELATION_KEY:
        return "{}/{}".format(qgroup_level(objectid), qgroup_subvid(objectid))
    if _type == UUID_KEY_SUBVOL or _type == UUID_KEY_RECEIVED_SUBVOL:
        return "0x{:0>16x}".format(objectid)

    if objectid == ROOT_TREE_OBJECTID and _type == DEV_ITEM_KEY:
        return 'DEV_ITEMS'
    if objectid == DEV_STATS_OBJECTID and _type == PERSISTENT_ITEM_KEY:
        return 'DEV_STATS'
    if objectid == FIRST_CHUNK_TREE_OBJECTID and _type == CHUNK_ITEM_KEY:
        return 'FIRST_CHUNK_TREE'
    if objectid == ULLONG_MAX:
        return '-1'

    return _key_objectid_str_map.get(objectid, str(objectid))


_key_str_objectid_map = {v: k for k, v in _key_objectid_str_map.items()}
_key_str_objectid_map.update({
    'DEV_ITEMS': ROOT_TREE_OBJECTID,
    'DEV_STATS': DEV_STATS_OBJECTID,
    'FIRST_CHUNK_TREE': FIRST_CHUNK_TREE_OBJECTID,
})

_re_qgroup_objectid = re.compile(r'^(?P<level>\d+)/(?P<subvid>\d+)$')


def _key_str_objectid(objectid_str, _type):
    # is it just a number?
    try:
        objectid = int(objectid_str)
        if objectid > -256 and objectid <= ULLONG_MAX:
            return objectid
    except ValueError:
        pass
    # is it known text?
    if objectid_str in _key_str_objectid_map:
        return _key_str_objectid_map[objectid_str]
    # is it a qgroup identifier?
    if _type in (QGROUP_RELATION_KEY, QGROUP_INFO_KEY, QGROUP_LIMIT_KEY):
        match = _re_qgroup_objectid.match(objectid_str)
        if match is not None:
            return _qgroup_objectid(**match.groupdict())
        else:
            raise ValueError("Unparseable key objectid {} for qgroup type {}".format(
                objectid_str, _key_type_str(_type)))
    # is it some UUID hex string?
    if objectid_str.startswith('0x'):
        try:
            return int(objectid_str, 0)
        except Exception:
            pass
    # otherwise, we don't know
    raise ValueError("Unparseable key objectid {}".format(objectid_str))


_key_type_str_map = {
    INODE_ITEM_KEY: 'INODE_ITEM',
    INODE_REF_KEY: 'INODE_REF',
    INODE_EXTREF_KEY: 'INODE_EXTREF',
    XATTR_ITEM_KEY: 'XATTR_ITEM',
    ORPHAN_ITEM_KEY: 'ORPHAN_ITEM',
    DIR_LOG_ITEM_KEY: 'DIR_LOG_ITEM',
    DIR_LOG_INDEX_KEY: 'DIR_LOG_INDEX',
    DIR_ITEM_KEY: 'DIR_ITEM',
    DIR_INDEX_KEY: 'DIR_INDEX',
    EXTENT_DATA_KEY: 'EXTENT_DATA',
    EXTENT_CSUM_KEY: 'EXTENT_CSUM',
    ROOT_ITEM_KEY: 'ROOT_ITEM',
    ROOT_BACKREF_KEY: 'ROOT_BACKREF',
    ROOT_REF_KEY: 'ROOT_REF',
    EXTENT_ITEM_KEY: 'EXTENT_ITEM',
    METADATA_ITEM_KEY: 'METADATA_ITEM',
    TREE_BLOCK_REF_KEY: 'TREE_BLOCK_REF',
    EXTENT_DATA_REF_KEY: 'EXTENT_DATA_REF',
    SHARED_BLOCK_REF_KEY: 'SHARED_BLOCK_REF',
    SHARED_DATA_REF_KEY: 'SHARED_DATA_REF',
    BLOCK_GROUP_ITEM_KEY: 'BLOCK_GROUP_ITEM',
    FREE_SPACE_INFO_KEY: 'FREE_SPACE_INFO',
    FREE_SPACE_EXTENT_KEY: 'FREE_SPACE_EXTENT',
    FREE_SPACE_BITMAP_KEY: 'FREE_SPACE_BITMAP',
    DEV_EXTENT_KEY: 'DEV_EXTENT',
    DEV_ITEM_KEY: 'DEV_ITEM',
    CHUNK_ITEM_KEY: 'CHUNK_ITEM',
    QGROUP_STATUS_KEY: 'QGROUP_STATUS',
    QGROUP_INFO_KEY: 'QGROUP_INFO',
    QGROUP_LIMIT_KEY: 'QGROUP_LIMIT',
    QGROUP_RELATION_KEY: 'QGROUP_RELATION',
    DEV_REPLACE_KEY: 'DEV_REPLACE',
    UUID_KEY_SUBVOL: 'UUID_KEY_SUBVOL',
    UUID_KEY_RECEIVED_SUBVOL: 'UUID_KEY_RECEIVED_SUBVOL',
    STRING_ITEM_KEY: 'STRING_ITEM',
    TEMPORARY_ITEM_KEY: 'TEMPORARY_ITEM',
    PERSISTENT_ITEM_KEY: 'PERSISTENT_ITEM',
}


def _key_type_str(_type):
    return _key_type_str_map.get(_type, str(_type))


_key_str_type_map = {v: k for k, v in _key_type_str_map.items()}


def _key_str_type(type_str):
    # is it just a number?
    try:
        type_ = int(type_str)
    except ValueError:
        pass
    else:
        if type_ >= -1 and type_ <= 255:
            return type_
    if type_str in _key_str_type_map:
        return _key_str_type_map[type_str]
    raise ValueError("Unknown key type {}".format(type_str))


def _key_offset_str(offset, _type):
    if _type == QGROUP_RELATION_KEY or _type == QGROUP_INFO_KEY or _type == QGROUP_LIMIT_KEY:
        return "{}/{}".format(qgroup_level(offset), qgroup_subvid(offset))
    if _type == UUID_KEY_SUBVOL or _type == UUID_KEY_RECEIVED_SUBVOL:
        return "0x{:0>16x}".format(offset)
    if offset == ULLONG_MAX:
        return '-1'
    if _type == ROOT_ITEM_KEY:
        return _key_objectid_str_map.get(offset, str(offset))

    return str(offset)


def _key_str_offset(offset_str, _type):
    # is it just a number?
    try:
        offset = int(offset_str)
    except ValueError:
        pass
    else:
        if offset >= -1 and offset <= ULLONG_MAX:
            return offset
    # is it a qgroup identifier?
    if _type in (QGROUP_RELATION_KEY, QGROUP_INFO_KEY, QGROUP_LIMIT_KEY):
        match = _re_qgroup_objectid.match(offset_str)
        if match is not None:
            return _qgroup_objectid(**{k: int(v) for k, v in match.groupdict().items()})
        else:
            raise ValueError("Unparseable key offset {} for qgroup type {}".format(
                offset_str, _key_type_str(_type)))
    # is it some UUID hex string?
    if offset_str.startswith('0x'):
        try:
            return int(offset_str, 0)
        except Exception:
            pass
    # otherwise, we don't know
    raise ValueError("Unparseable key offset {}".format(offset_str))


class ItemNotFoundError(IndexError):
    """Helper exception for lookup convenience functions.

    If a convenience function on a :class:`btrfs.ctree.FileSystem` object is
    supposed to return exactly one object at a specific location, and no object
    is found, this type of exception is raised.

    An example is the :func:`~btrfs.ctree.FileSystem.block_group` helper, which
    raises this error if no block group item is found at the exact specified
    location.
    """
    pass


KEY_MAX = (1 << 136) - 1


class Key(object):
    """Btrfs metadata trees have a key space of 136-bit numbers.

    A full 136-bit tree key is composed as:
      (objectid << 72) + (type << 64) + offset

    :param objectid: 64-bit object ID number or string representation.
    :type objectid: Union[int, str]
    :param type\_: 8-bit type number or string representation.
    :type type\_: Union[int, str]
    :param int offset: 64-bit offset number or string representation.
    :type offset: Union[int, str]

    Key objects support sorting and simple addition and subtraction.  Also,
    when subtracting 1 from a zero key, the value wraps around to the largest
    value possible, vice versa.

    Example::

        >>> key1 = btrfs.ctree.Key(425, 'DIR_ITEM', 17818406)
        >>> key1
        Key(425, 84, 17818406)
        >>> str(key1)
        '(425 DIR_ITEM 17818406)'
        >>> key2 = btrfs.ctree.Key(442, btrfs.ctree.EXTENT_DATA_KEY, 0)
        >>> key2 > key1
        True

        >>> min_key = btrfs.ctree.Key(0, 0, 0)
        >>> min_key
        Key(0, 0, 0)
        >>> str(min_key)
        '(0 0 0)'
        >>> min_key - 1
        Key(18446744073709551615, 255, 18446744073709551615)
        >>> str(min_key - 1)
        '(-1 255 -1)'

    The `-1` value in the string representation is just a convenience way to
    write the maximum allowed number. The actual value for a 64 bit numer is
    still 18446744073709551615, and for 8 bit that's 255 of course.

    For example, when setting up a minimum and maximum key for a metadata
    search, the arithmetic that can be done helps quickly defining the maximum
    value. The next example shows the key range for finding all intormation
    about an inode in a filesystem tree:

    Example::

        >>> inum = 31337
        >>> min_key = btrfs.ctree.Key(inum, 0, 0)
        >>> max_key = btrfs.ctree.Key(inum + 1, 0, 0) - 1
        >>>
        >>> min_key
        Key(31337, 0, 0)
        >>> max_key
        Key(31337, 255, 18446744073709551615)

    Last but not least, the utils module contains the helper function
    :func:`~btrfs.utils.parse_key_string` to dissect a full text key string:

    Example::

        >>> btrfs.utils.parse_key_string('(535 EXTENT_DATA 0)')
        Key(535, 108, 0)
    """

    def __init__(self, objectid, type_, offset):
        if isinstance(type_, int):
            self._type = U8(type_)
        elif isinstance(type_, str):
            self._type = U8(_key_str_type(type_))
        else:
            raise ValueError("Key type needs to be either string or integer: {}.".format(type_))
        if isinstance(objectid, int):
            self._objectid = ULL(objectid)
        elif isinstance(objectid, str):
            self._objectid = ULL(_key_str_objectid(objectid, self._type))
        else:
            raise ValueError("Key objectid needs to be either string or integer: {}.".format(
                objectid))
        if isinstance(offset, int):
            self._offset = ULL(offset)
        elif isinstance(offset, str):
            self._offset = ULL(_key_str_offset(offset, self._type))
        else:
            raise ValueError("Key offset needs to be either string or integer: {}.".format(
                offset))
        self._pack()

    @property
    def objectid(self):
        """Key Object ID"""
        return self._objectid

    @objectid.setter
    def objectid(self, _objectid):
        self._objectid = _objectid
        self._pack()

    @property
    def type(self):
        """Key Type"""
        return self._type

    @type.setter
    def type(self, _type):
        self._type = _type
        self._pack()

    @property
    def offset(self):
        """Key Offset"""
        return self._offset

    @offset.setter
    def offset(self, _offset):
        self._offset = _offset
        self._pack()

    @property
    def key(self):
        """Full numeric 136-bit key value."""
        return self._key

    @key.setter
    def key(self, _key):
        self._key = _key & KEY_MAX
        self._unpack()

    def _pack(self):
        self._key = (self.objectid << 72) + (self._type << 64) + self.offset

    def _unpack(self):
        self._objectid = ULL(self._key >> 72)
        self._type = U8(self._key >> 64)
        self._offset = ULL(self._key)

    def __lt__(self, other):
        if isinstance(other, Key):
            return self._key < other._key
        return self._key < other

    def __le__(self, other):
        if isinstance(other, Key):
            return self._key <= other._key
        return self._key <= other

    def __eq__(self, other):
        if isinstance(other, Key):
            return self._key == other._key
        return self._key == other

    def __ge__(self, other):
        if isinstance(other, Key):
            return self._key >= other._key
        return self._key >= other

    def __gt__(self, other):
        if isinstance(other, Key):
            return self._key > other._key
        return self._key > other

    def __repr__(self):
        return "Key({}, {}, {})".format(self._objectid, self._type, self._offset)

    def __str__(self):
        return "({} {} {})".format(
            _key_objectid_str(self._objectid, self._type),
            _key_type_str(self._type),
            _key_offset_str(self._offset, self._type),
        )

    def __add__(self, amount):
        new_key = copy.copy(self)
        new_key.key += amount
        return new_key

    def __sub__(self, amount):
        new_key = copy.copy(self)
        new_key.key -= amount
        return new_key


class DiskKey(Key):
    """Object representation of struct `btrfs_disk_key`.

    Objects of this type are used in metadata search results.
    """
    _disk_key = struct.Struct('<QBQ')

    def __init__(self, data):
        super(DiskKey, self).__init__(*DiskKey._disk_key.unpack_from(data))


class FileSystem(object):
    """The FileSystem object is a bit of a spider in the web of this library.
    It contains a lot of convenience methods providing quick access to all
    kinds of functionality.

    :param str path: Path to the mounted filesystem.

    :ivar str path: The filesystem path used to initialize this object.
    :ivar uuid.UUID fsid: Filesystem ID.
    :ivar int nodesize: B-tree node size (same as leaf size).
    :ivar int sectorsize: Smallest allocatable block size in bytes for storing
        data.

    The fsid, nodesize and sectorsize values are cached from a call to
    :func:`~btrfs.ctree.FileSystem.fs_info` when initializing the object.

    It is highly recommended to use the built in context manager. Doing so
    prevents leaking the internal open file descriptor.

    Example::

        >>> with btrfs.ctree.FileSystem('/') as fs:
        ...     print(fs.top_level().generation)
        ...
        3382004
    """
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY)
        _fs_info = self.fs_info()
        self.fsid = _fs_info.fsid
        self.nodesize = _fs_info.nodesize
        self.sectorsize = _fs_info.sectorsize

    def __enter__(self):
        return self

    def fs_info(self):
        """
        :returns: General filesystem information.
        :rtype: :class:`btrfs.ioctl.FsInfo`
        """
        return btrfs.ioctl.fs_info(self.fd)

    def dev_info(self, devid):
        """
        :param int devid: Device ID.
        :returns: Device information.
        :rtype: :class:`btrfs.ioctl.DevInfo`
        """
        return btrfs.ioctl.dev_info(self.fd, devid)

    def dev_stats(self, devid, reset=False):
        """
        :param int devid: Device ID.
        :param bool reset: Reset device error counters to zero.
        :returns: Device statistics.
        :rtype: :class:`btrfs.ioctl.DevStats`
        """
        return btrfs.ioctl.dev_stats(self.fd, devid, reset)

    def space_info(self):
        """
        :returns: Space information
        :rtype: List[:class:`btrfs.ioctl.SpaceInfo`]
        """
        return btrfs.ioctl.space_info(self.fd)

    def search(self, tree, min_key=None, max_key=None):
        """
        Retrieve all metadata items within a specific range. This is basically
        a thin wrapper around the :func:`~btrfs.ioctl.search_v2` with a bit
        limited functionality, but suited for almost all use cases when quickly
        searching around.

        :param int tree: The metadata tree we're searching in.
        :param btrfs.ctree.Key min_key: Minimum key value for items to return.
        :param btrfs.ctree.Key max_key: Maximum key value for items to return.
        :returns: Any metadata item found in the search range, as sub class of
            :class:`~btrfs.ctree.ItemData`, helped by the
            :func:`btrfs.ctree.classify` function.
        :rtype: Iterator[:class:`~btrfs.ctree.ItemData`]
        """
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            yield btrfs.ctree.classify(header, data)

    def devices(self, min_devid=1, max_devid=ULLONG_MAX):
        """
        :param int min_devid: Lowest Device ID to search for.
        :param int max_devid: Highest Device ID to search for.
        :returns: Device Items from the Chunk tree.
        :rtype: Iterator[:class:`~btrfs.ctree.DevItem`]
        """
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(DEV_ITEMS_OBJECTID, DEV_ITEM_KEY, min_devid)
        max_key = Key(DEV_ITEMS_OBJECTID, DEV_ITEM_KEY, max_devid)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            yield DevItem(header, data)

    def chunks(self, min_vaddr=0, max_vaddr=ULLONG_MAX, nr_items=None):
        """
        :param int min_vaddr: Lowest virtual address to search for.
        :param int max_vaddr: Highest virtual address to search for.
        :param int nr_items: Maximum amount of items to return. Defaults to no limit.
        :returns: Chunk items from the Chunk tree.
        :rtype: Iterator[:class:`~btrfs.ctree.Chunk`]
        """
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, min_vaddr)
        max_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, max_vaddr)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key,
                                                  nr_items=nr_items):
            yield Chunk(header, data)

    def dev_extents(self, min_devid=1, max_devid=ULLONG_MAX):
        """
        :param int min_devid: Lowest Device ID to search for.
        :param int max_devid: Highest Device ID to search for.
        :returns: Device Extent Items from the Device tree.
        :rtype: Iterator[:class:`~btrfs.ctree.DevExtent`]
        """
        tree = DEV_TREE_OBJECTID
        min_key = btrfs.ctree.Key(min_devid, 0, 0)
        max_key = btrfs.ctree.Key(max_devid, 255, ULLONG_MAX)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            yield DevExtent(header, data)

    def block_group(self, vaddr, length=None):
        """
        :param int vaddr: Starting virtual address of the block group.
        :param int length: Block group length (optional). If this information
            is already known, it can be used to construct an exact match for
            the search key.
        :returns: Block Group Item
        :rtype: :class:`~btrfs.ctree.BlockGroupItem`
        :raises: :class:`ItemNotFoundError` if no Block Group Item can be found
            at the address.
        """
        tree = EXTENT_TREE_OBJECTID
        min_offset = length if length is not None else 0
        max_offset = length if length is not None else ULLONG_MAX
        min_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, min_offset)
        max_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, max_offset)
        block_groups = [BlockGroupItem(header, data)
                        for header, data in
                        btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key, nr_items=1)]
        if len(block_groups) == 0:
            raise ItemNotFoundError("No block group at vaddr {}".format(vaddr))
        return block_groups[0]

    def extents(self, min_vaddr=0, max_vaddr=ULLONG_MAX,
                load_data_refs=False, load_metadata_refs=False):
        """
        :param int min_vaddr: Lowest virtual address to search for.
        :param int max_vaddr: Highest virtual address to search for.
        :param bool load_data_refs: Parse and load backreference information
            for data extents.
        :param bool load_metadata_refs: Parse and load backreference
            information for metadata extents.
        :returns: Extent and MetaData Items from the Extent tree
        :rtype: Iterator[Union[:class:`ExtentItem`, :class:`MetaDataItem`]]

        The 'refs' are backreference information. These sub items are stored
        inside the :class:`ExtentItem` and :class:`MetaDataItem` Items, and
        overflow to separately indexed items. When dealing with search results
        in user space, these backreferences are of little use to us, since the
        search API only allows us to search in tree leaves. So, they're ignored
        by default.
        """
        tree = EXTENT_TREE_OBJECTID
        min_key = Key(min_vaddr, 0, 0)
        max_key = Key(max_vaddr, 255, ULLONG_MAX)
        extent = None
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            if header.type == EXTENT_ITEM_KEY:
                if extent is not None:
                    yield extent
                extent = ExtentItem(header, data, load_data_refs=load_data_refs,
                                    load_metadata_refs=load_metadata_refs)
            elif header.type == METADATA_ITEM_KEY:
                if extent is not None:
                    yield extent
                extent = MetaDataItem(header, data, load_refs=load_metadata_refs)
            elif header.type == EXTENT_DATA_REF_KEY:
                if load_data_refs:
                    extent._append_extent_data_ref(ExtentDataRef(header, data))
            elif header.type == SHARED_DATA_REF_KEY:
                if load_data_refs:
                    extent._append_shared_data_ref(SharedDataRef(header, data))
            elif header.type == TREE_BLOCK_REF_KEY:
                if load_metadata_refs:
                    extent._append_tree_block_ref(TreeBlockRef(header))
            elif header.type == SHARED_BLOCK_REF_KEY:
                if load_metadata_refs:
                    extent._append_shared_block_ref(SharedBlockRef(header))
            elif header.type != BLOCK_GROUP_ITEM_KEY:
                raise Exception("BUG: unexpected object {}".format(
                    Key(header.objectid, header.type, header.offset)))

        if extent is not None:
            yield extent

    def top_level(self):
        """
        :returns: The top level subvolume with ID 5, a.k.a. `FS_TREE_OBJECTID`.
        :rtype: :class:`RootItem`
        """
        return list(self.subvolumes(min_id=FS_TREE_OBJECTID, max_id=FS_TREE_OBJECTID))[0]

    def subvolumes(self, min_id=FIRST_FREE_OBJECTID, max_id=LAST_FREE_OBJECTID):
        """
        :param int min_id: Lowest subvolume ID to search for.
        :param int max_id: Highest subvolume ID to search for.
        :returns: Root Items from the Root tree, containing subvolume information.
        :rtype: Iterator[:class:`RootItem`]
        """
        tree = ROOT_TREE_OBJECTID
        if min_id == max_id:
            min_type = ROOT_ITEM_KEY
            max_type = ROOT_ITEM_KEY
        else:
            min_type = 0
            max_type = 255
        min_key = Key(min_id, min_type, 0)
        max_key = Key(max_id, max_type, ULLONG_MAX)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            if header.type != ROOT_ITEM_KEY:
                continue
            yield RootItem(header, data)

    def orphan_subvol_ids(self):
        """
        :returns: ObjectID numbers of orphaned items in the Root tree.
        :rtype: List[int]
        """
        tree = ROOT_TREE_OBJECTID
        min_key = Key(ORPHAN_OBJECTID, ORPHAN_ITEM_KEY, 0)
        max_key = Key(ORPHAN_OBJECTID, ORPHAN_ITEM_KEY, ULLONG_MAX)
        subvol_ids = [header.offset
                      for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key)]
        return subvol_ids

    def free_space_extents(self, min_vaddr=0, max_vaddr=ULLONG_MAX):
        """
        :param int min_vaddr: Minimum virtual address when searching for free space.
        :param int max_vaddr: Maximum virtual address when searching for free space.
        :returns: Free space extent information from the Free Space Tree.
        :rtype: Iterator[:class:`btrfs.free_space_tree.FreeSpaceExtent`]

        .. note::

            The Free Space Tree can contain both Free Space Extent Items and
            Free Space Bitmap Items, which contain a more compact
            representation of free space extents. This helper function will
            transparently unpack these bitmaps and return one type of helper
            object, the :class:`~btrfs.free_space_tree.FreeSpaceExtent`
            object.
        """
        tree = FREE_SPACE_TREE_OBJECTID
        min_key = Key(min_vaddr, 0, 0)
        max_key = Key(max_vaddr, 255, ULLONG_MAX)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            if header.type == FREE_SPACE_EXTENT_KEY:
                yield btrfs.free_space_tree.FreeSpaceExtent(header.objectid, header.offset)
            elif header.type == FREE_SPACE_BITMAP_KEY:
                yield from FreeSpaceBitmap(header, data).unpack(self.sectorsize)
            elif header.type != FREE_SPACE_INFO_KEY:
                raise Exception("BUG: unexpected object {}".format(
                    Key(header.objectid, header.type, header.offset)))

    def sync(self):
        """Call the btrfs sync kernel function, causing a transaction commit."""
        btrfs.ioctl.sync(self.fd)

    def features(self):
        """
        :returns: Filesystem Features.
        :rtype: :class:`btrfs.ioctl.FeatureFlags`
        """
        return btrfs.ioctl.get_features(self.fd)

    def mixed_groups(self):
        """
        :returns: True if this filesystem used mixed block groups with metadata
            and data in the same block groups, else False.
        :rtype: bool
        """
        return self.features().incompat_flags & btrfs.ioctl.FEATURE_INCOMPAT_MIXED_GROUPS != 0

    def usage(self):
        """
        :returns: Detailed filesystem usage information.
        :rtype: :class:`btrfs.fs_usage.FsUsage`
        """
        return btrfs.fs_usage.FsUsage(self)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.close(self.fd)


class ItemData(object):
    """ItemData is a base class for all tree item types.

    :ivar key: Key under which this item is stored in the tree.
    :type key: :class:`~btrfs.ctree.Key`
    """
    def __init__(self, header):
        if isinstance(header, btrfs.ioctl.SearchHeader):
            self.key = Key(header.objectid, header.type, header.offset)
        elif header is not None:
            raise TypeError("Not a SearchHeader: {}".format(header))

    def _setattr_from_key(self, objectid_attr=None, type_attr=None, offset_attr=None):
        if objectid_attr is not None:
            setattr(self, objectid_attr, self.key.objectid)
        if type_attr is not None:
            setattr(self, type_attr, self.key.type)
        if offset_attr is not None:
            setattr(self, offset_attr, self.key.offset)
        self._key_attrs = objectid_attr, type_attr, offset_attr

    def __lt__(self, other):
        return self.key < other.key


class SubItem(object):
    pass


class DevItem(ItemData):
    """Object representation of struct `btrfs_dev_item`.

    A `DevItem` contains information about a single block device that is
    attached to the filesystem.

    * Tree: `CHUNK_TREE_OBJECTID` (3)
    * Key objectid: `DEV_ITEMS_OBJECTID` (1)
    * Key type: `DEV_ITEM_KEY` (216)
    * Key offset: Device ID.

    :ivar int devid: Device ID.
    :ivar int total_bytes: Total amount of bytes.
    :ivar int bytes_used: Total amount of allocated bytes.
    :ivar int io_align: *Not used*, set to same value as sector_size.
    :ivar int io_width: *Not used*, set to same value as sector_size.
    :ivar int sector_size: Smallest IO block size to use.
    :ivar int type: *Not used*
    :ivar int generation: *Not used*
    :ivar int start_offset: *Not used*
    :ivar int dev_group: *Not used*
    :ivar int seek_speed: *Not used*
    :ivar int bandwidth: *Not used*
    :ivar uuid.UUID uuid: Device UUID.
    :ivar uuid.UUID fsid: Filesystem ID.

    """
    _dev_item = struct.Struct('<3Q3L3QL2B16s16s')

    def __init__(self, header, data):
        super().__init__(header)
        self.devid, self.total_bytes, self.bytes_used, self.io_align, self.io_width, \
            self.sector_size, self.type, self.generation, self.start_offset, self.dev_group, \
            self.seek_speed, self.bandwidth, uuid_bytes, fsid_bytes = \
            DevItem._dev_item.unpack(data)
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.fsid = uuid.UUID(bytes=fsid_bytes)

    def __str__(self):
        return "dev item devid {self.devid} uuid {self.uuid} bytes_used {self.bytes_used} " \
            "total_bytes {self.total_bytes}".format(self=self)


class Chunk(ItemData):
    """Object representation of struct `btrfs_chunk`.

    A `Chunk` is a piece of virtual address space. A `Chunk` has a 1 to 1
    relationship to a :class:`BlockGroupItem`, and a 1 to many relationship
    with a fixed amount of :class:`Stripe` objects.

    * Tree: `CHUNK_TREE_OBJECTID` (3)
    * Key objectid: `FIRST_CHUNK_TREE_OBJECTID` (256)
    * Key type: `CHUNK_ITEM_KEY` (228)
    * Key offset: Virtual address.

    :ivar int vaddr: Virtual address where the Chunk starts (taken from the
        offset field of the item key).
    :ivar int length: Chunk length in bytes,
    :ivar int owner: Extent tree the chunk belongs to. *Not used*, always 2
        now.
    :ivar int stripe_len: Hardcoded to `BTRFS_STRIPE_LEN`, which is 64kiB.
    :ivar int type: Block group flags for the corresponding block group. So, a
        Chunk **type** contains both Block Group **type** and **profile**.
    :ivar int io_align: *Not used*, see `stripe_len`.
    :ivar int io_width: *Not used*, see `stripe_len`.
    :ivar int sector_size: Smallest IO block size to use.
    :ivar int num_stripes: Amount of :class:`Stripe` (or, also the amount of
        :class:`Device Extent`) objects related to this `Chunk`.
    :ivar int sub_stripes: A hack for `RAID10`. For `RAID10` this value is 2,
        otherwise 1.
    :ivar stripes: :class:`Stripe` Items that are stored inside this Chunk Item.
    :vartype stripes: List[:class:`Stripe`]
    """
    _chunk = struct.Struct('<4Q3L2H')

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(offset_attr='vaddr')
        self.length, self.owner, self.stripe_len, self.type, self.io_align, \
            self.io_width, self.sector_size, self.num_stripes, self.sub_stripes = \
            Chunk._chunk.unpack_from(data)
        self.stripes = []
        pos = Chunk._chunk.size
        for i in range(self.num_stripes):
            next_pos = pos + Stripe._stripe.size
            self.stripes.append(Stripe(data[pos:next_pos]))
            pos = next_pos

    def __str__(self):
        return "chunk vaddr {self.vaddr} type {self.type_str} length {self.length_str} " \
            "num_stripes {self.num_stripes}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'length'),
            (btrfs.utils.pretty_size, 'stripe_len'),
            (btrfs.utils.pretty_size, 'io_align'),
            (btrfs.utils.pretty_size, 'io_width'),
            (btrfs.utils.pretty_size, 'sector_size'),
            (btrfs.utils.block_group_flags_str, 'type'),
        ]


class Stripe(SubItem):
    """Object representation of struct `btrfs_stripe`.

    A list of `Stripe` items is hidden inside the `Chunk` item and each of them
    contains information that points to the beginning of a `Device Extent`,
    which is an actual allocated piece of physical disk space in which data
    ends up that is written to the virtual address space of the `Chunk`.

    :ivar int devid: Device ID of the device that holds the `Device Extent`.
    :ivar int offset: Physical address on the device where the `Device Extent` starts.
    :ivar uuid.UUID uuid: Device UUID of the device with the above listed devid.
    """
    _stripe = struct.Struct('<2Q16s')

    def __init__(self, data):
        self.devid, self.offset, uuid_bytes = Stripe._stripe.unpack(data)
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "stripe devid {self.devid} offset {self.offset}".format(self=self)


class DevExtent(ItemData):
    """Object representation of struct `btrfs_dev_extent`.

    The `Device Extent` is a range of physical address space allocated from one
    of the attached devices and used by a `Chunk` to store data.

    * Tree: `DEV_TREE_OBJECTID` (4)
    * Key objectid: Device ID.
    * Key type: `DEV_EXTENT_KEY` (204)
    * Key offset: Physical address.

    :ivar int devid: Device ID of the device that holds this `Device Extent`
        (taken from the objectid field of the item key).
    :ivar int paddr: Physical address on the device where the `Device Extent`
        starts (taken from the offset field of the item key).
    :ivar int chunk_tree: Chunk tree the device extent belongs to. This is
        always 3 now.
    :ivar int chunk_offset: Virtual address of the related `Chunk`.
    :ivar int length: Length in physical bytes.
    :ivar uuid.UUID chunk_tree_uuid: UUID of the chunk tree that this `Device
        Extent` belongs to. This is currently always the UUID of tree 3.
    """
    _dev_extent = struct.Struct('<4Q16s')

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='devid', offset_attr='paddr')
        self.chunk_tree, self.chunk_objectid, self.chunk_offset, self.length, \
            chunk_tree_uuid_bytes = DevExtent._dev_extent.unpack(data)
        self.chunk_tree_uuid = uuid.UUID(bytes=chunk_tree_uuid_bytes)

    @property
    def vaddr(self):
        """Alias for the chunk_offset attribute."""
        return self.chunk_offset

    def __str__(self):
        return "dev extent devid {self.devid} paddr {self.paddr} length {self.length_str} " \
            "chunk {self.chunk_offset}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'length'),
        ]


class BlockGroupItem(ItemData):
    """Object representation of struct `btrfs_block_group_item`.

    The `Block Group` has a 1 to 1 relationship with a `Chunk` and tracks some
    usage information about a range of virtual address space.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key objectid: Virtual address.
    * Key type: `BLOCK_GROUP_ITEM_KEY` (192)
    * Key offset: Block Group length.

    :ivar int vaddr: Virtual address where the Bock Group starts (taken from
        the objectid field of the item key).
    :ivar int length: Block Group length in bytes (taken from the offset field
        of the item key).
    :ivar int used: Amount of bytes used by Extents in the Block Group.
    :ivar int chunk_objectid: Object ID of the Chunk this Block Group relates
        to. Currently always 256.
    :ivar int flags: Type and profile for this Block Group. e.g. 0x11, which is
        `DATA|RAID1`.
    """
    _block_group_item = struct.Struct('<3Q')

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='vaddr', offset_attr='length')
        self.used, self.chunk_objectid, self.flags = \
            BlockGroupItem._block_group_item.unpack(data)

    @property
    def used_pct(self):
        """Convenience property that calculates the percentage of usage."""
        return int(round((self.used * 100) / self.length))

    def __str__(self):
        return "block group vaddr {self.vaddr} length {self.length} " \
            "flags {self.flags_str} used {self.used} used_pct {self.used_pct}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'length'),
            (btrfs.utils.pretty_size, 'used'),
            (btrfs.utils.block_group_flags_str, 'flags'),
        ]


class ExtentItem(ItemData):
    """Object representation of struct `btrfs_extent_item`.

    An :class:`ExtentItem` lives in the Extent Tree and tracks information
    about a piece of virtual address space that is in use. A FileExtentItem
    object from a subvolume tree can point to it, to let us know a file in the
    filesystem uses part of this extent.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key objectid: Virtual address.
    * Key type: `EXTENT_ITEM_KEY` (168)
    * Key offset: Extent length.

    If the `skinny_metadata` feature is enabled in the filesystem, then
    metadata extents are stored separately as :class:`MetaDataItem`.

    An :class:`ExtentItem` includes inline backreference items. In the kernel,
    this information is used to be able to find out which different inodes in
    subvolume trees are using data from this extent. For us, in userspace, this
    information is not very relevant, since we cannot look into B-tree nodes
    using the kernel search API. So, by default the backreference information
    is ignored when creating these kind of objects from a metadata search.

    Instead, to find out who is referencing data from an extent, the
    :func:`btrfs.ioctl.logical_to_ino` and
    :func:`btrfs.ioctl.logical_to_ino_v2` functions can be used.

    :ivar int vaddr: Virtual address where the Extent starts (taken from the
        objectid field of the item key).
    :ivar int length: Length of the extent in bytes (taken from the offset
        field of the item key).
    :ivar int refs: Amount of explicit references to this extent.
    :ivar int generation: Generation of the filesystem when this extent was
        created.
    :ivar int flags: Some flags describing which type of extent this is.

    The flags are an or-ed combination of one or more of the following values
    (available as attribute of this module):

    - EXTENT_FLAG_DATA: This extent contains data.
    - EXTENT_FLAG_TREE_BLOCK: This extent contains a metadata tree block.
    - BLOCK_FLAG_FULL_BACKREF: The tree block backreference contains a full
      back reference.

    When backreference information is being loaded, there are a few additional
    lists present in this object. Also, when using the
    :func:`FileSystem.extents` helper to retrieve extent information, then
    separately stored backreference items which do not fit into the extent item
    itself any more are also appended to these lists:

    If the extent is a data extent, then this object contains:

    :ivar extent_data_refs: Indirect back references.
    :vartype extent_data_refs: List[Union[:class:`InlineExtentDataRef`,
        :class:`ExtentDataRef`]]
    :ivar shared_data_refs: Shared back references.
    :vartype shared_data_refs: List[Union[:class:`InlineSharedDataRef`,
        :class:`SharedDataRef`]]

    If the extent is a metadata tree block, then this object contains:

    :ivar tree_block_refs: Tree block backreferences.
    :vartype tree_block_refs: List[Union[:class:`InlineTreeBlockRef`,
        :class:`TreeBlockRef`]]
    :ivar shared_block_refs: Shared tree block backreferences.
    :vartype shared_block_refs: List[Union[:class:`InlineSharedBlockRef`,
        :class:`SharedBlockRef`]]

    Further documentation of backreferences is out of scope for this module.
    Please refer to the btrfs wiki about resolving extent backreferences for
    more information.
    """
    _extent_item = struct.Struct('<3Q')
    _extent_inline_ref = struct.Struct('<BQ')

    def __init__(self, header, data, load_data_refs=True, load_metadata_refs=True):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='vaddr', offset_attr='length')
        pos = 0
        self.refs, self.generation, self.flags = ExtentItem._extent_item.unpack_from(data, pos)
        pos += ExtentItem._extent_item.size
        if self.flags == EXTENT_FLAG_DATA and load_data_refs:
            self.extent_data_refs = []
            self.shared_data_refs = []
            while pos < len(data):
                inline_ref_type, inline_ref_offset = \
                    ExtentItem._extent_inline_ref.unpack_from(data, pos)
                if inline_ref_type == EXTENT_DATA_REF_KEY:
                    pos += 1
                    next_pos = pos + InlineExtentDataRef._inline_extent_data_ref.size
                    self.extent_data_refs.append(InlineExtentDataRef(data[pos:next_pos]))
                    pos = next_pos
                elif inline_ref_type == SHARED_DATA_REF_KEY:
                    pos += 1
                    next_pos = pos + InlineSharedDataRef._inline_shared_data_ref.size
                    self.shared_data_refs.append(InlineSharedDataRef(data[pos:next_pos]))
                    pos = next_pos
        elif self.flags & EXTENT_FLAG_TREE_BLOCK and load_metadata_refs:
            next_pos = pos + TreeBlockInfo._tree_block_info.size
            self.tree_block_info = TreeBlockInfo(data[pos:next_pos])
            pos = next_pos
            self.tree_block_refs = []
            self.shared_block_refs = []
            while pos < len(data):
                inline_ref_type, inline_ref_offset = \
                    ExtentItem._extent_inline_ref.unpack_from(data, pos)
                if inline_ref_type == TREE_BLOCK_REF_KEY:
                    self.tree_block_refs.append(InlineTreeBlockRef(inline_ref_offset))
                elif inline_ref_type == SHARED_BLOCK_REF_KEY:
                    self.shared_block_refs.append(InlineSharedBlockRef(inline_ref_offset))
                else:
                    raise Exception("BUG: expected inline TREE_BLOCK_REF or SHARED_BLOCK_REF_KEY "
                                    "but got inline_ref_type {}".format(inline_ref_type))
                pos += ExtentItem._extent_inline_ref.size

    def _append_extent_data_ref(self, ref):
        self.extent_data_refs.append(ref)

    def _append_shared_data_ref(self, ref):
        self.shared_data_refs.append(ref)

    def _append_tree_block_ref(self, ref):
        self.tree_block_refs.append(ref)

    def _append_shared_block_ref(self, ref):
        self.shared_block_refs.append(ref)

    def __str__(self):
        return "extent vaddr {self.vaddr} length {self.length} refs {self.refs} " \
            "gen {self.generation} flags {self.flags_str}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.extent_flags_str, 'flags'),
        ]


class ExtentDataRef(ItemData):
    """Object representation of struct `btrfs_extent_data_ref`.

    Documentation of this item is out of scope for this module. Please refer to
    the btrfs wiki about resolving extent backreferences for more information.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key type: `EXTENT_DATA_REF_KEY` (178)

    :ivar int root: root
    :ivar int objectid: objectid
    :ivar int offset: offset
    :ivar int count: count
    """
    _extent_data_ref = struct.Struct('<3QL')

    def __init__(self, header, data):
        super().__init__(header)
        self.root, self.objectid, self.offset, self.count = \
            ExtentDataRef._extent_data_ref.unpack(data)

    def __str__(self):
        return "extent data backref root {self.root} objectid {self.objectid} " \
            "offset {self.offset} count {self.count}".format(self=self)


class InlineExtentDataRef(ExtentDataRef):
    """Identical content to :class:`ExtentDataRef`, but the backreference was
    inlined in the extent item."""
    _inline_extent_data_ref = ExtentDataRef._extent_data_ref

    def __init__(self, data):
        self.root, self.objectid, self.offset, self.count = \
            InlineExtentDataRef._inline_extent_data_ref.unpack(data)

    def __str__(self):
        return "inline extent data backref root {self.root} objectid {self.objectid} " \
            "offset {self.offset} count {self.count}".format(self=self)


class SharedDataRef(ItemData):
    """Object representation of struct `btrfs_shared_data_ref`.

    Documentation of this item is out of scope for this module. Please refer to
    the btrfs wiki about resolving extent backreferences for more information.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key type: `SHARED_DATA_REF_KEY` (184)

    :ivar int parent: parent
    :ivar int count: count
    """
    _shared_data_ref = struct.Struct('<L')

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(offset_attr='parent')
        self.count, = SharedDataRef._shared_data_ref.unpack(data)

    def __str__(self):
        return "shared data backref parent {self.parent} count {self.count}".format(self=self)


class InlineSharedDataRef(SharedDataRef):
    """Identical content to :class:`SharedDataRef`, but the backreference was
    inlined in the extent item."""
    _inline_shared_data_ref = struct.Struct('<QL')

    def __init__(self, data):
        self.parent, self.count = InlineSharedDataRef._inline_shared_data_ref.unpack(data)

    def __str__(self):
        return "inline shared data backref parent {self.parent} " \
            "count {self.count}".format(self=self)


class TreeBlockInfo(SubItem):
    """Object representation of struct `btrfs_tree_block_info`.

    Documentation of this item is out of scope for this module. Please refer to
    the btrfs wiki about resolving extent backreferences for more information.

    :ivar key: key
    :vartype key: :class:`Key`
    :ivar int level: level
    """
    _tree_block_info = struct.Struct('<QBQB')

    def __init__(self, data):
        tb_objectid, tb_type, tb_offset, self.level = \
            TreeBlockInfo._tree_block_info.unpack(data)
        self.key = Key(tb_objectid, tb_type, tb_offset)

    def __str__(self):
        return "tree block key {self.key} level {self.level}".format(self=self)


class MetaDataItem(ItemData):
    """Object representation of struct `btrfs_metadata_item`.

    A :class:`MetaDataItem` lives in the Extent Tree and tracks information
    about a piece of virtual address space that is in use to store a metadata
    tree block.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key objectid: Virtual address.
    * Key type: `METADATA_ITEM_KEY` (169)
    * Key offset: Extent length.

    If the `skinny_metadata` filesystem feature is enabled, metadata extents
    are tracked using this item type, which encodes all necessecary data in a
    more compact way than using a regular extent item.

    :ivar int vaddr: Virtual address where the Extent starts (taken from the
        objectid field of the item key).
    :ivar int skinny_level: Tree level.
        field of the item key).
    :ivar int refs: Amount of explicit references to this extent.
    :ivar int generation: Generation of the filesystem when this extent was
        created.
    :ivar int flags: See below.

    The flags are an or-ed combination of one or more of the following values
    (available as attribute of this module):

    - EXTENT_FLAG_TREE_BLOCK: This extent contains a metadata tree block.
    - BLOCK_FLAG_FULL_BACKREF: The tree block backreference contains a full
      back reference.

    When backreference information is being loaded, there are a few additional
    lists present in this object. Also, when using the
    :func:`FileSystem.extents` helper to retrieve extent information, then
    separately stored backreference items which do not fit into the extent item
    itself any more are also appended to these lists:

    :ivar tree_block_refs: Tree block backreferences.
    :vartype tree_block_refs: List[Union[:class:`InlineTreeBlockRef`,
        :class:`TreeBlockRef`]]
    :ivar shared_block_refs: Shared tree block backreferences.
    :vartype shared_block_refs: List[Union[:class:`InlineSharedBlockRef`,
        :class:`SharedBlockRef`]]

    Further documentation of backreferences is out of scope for this module.
    Please refer to the btrfs wiki about resolving extent backreferences for
    more information.
    """
    def __init__(self, header, data, load_refs=True):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='vaddr', offset_attr='skinny_level')
        self.refs, self.generation, self.flags = ExtentItem._extent_item.unpack_from(data)
        if load_refs:
            self._load_refs(data[ExtentItem._extent_item.size:])

    def _load_refs(self, data):
        pos = 0
        self.tree_block_refs = []
        self.shared_block_refs = []
        while pos < len(data):
            inline_ref_type, inline_ref_offset = \
                ExtentItem._extent_inline_ref.unpack_from(data, pos)
            if inline_ref_type == TREE_BLOCK_REF_KEY:
                self.tree_block_refs.append(InlineTreeBlockRef(inline_ref_offset))
            elif inline_ref_type == SHARED_BLOCK_REF_KEY:
                self.shared_block_refs.append(InlineSharedBlockRef(inline_ref_offset))
            else:
                raise Exception("BUG: expected inline TREE_BLOCK_REF or SHARED_BLOCK_REF_KEY "
                                "in METADATA_ITEM {}, but got inline_ref_type {}"
                                "".format(self.key, inline_ref_type))
            pos += ExtentItem._extent_inline_ref.size

    def _append_tree_block_ref(self, ref):
        self.tree_block_refs.append(ref)

    def _append_shared_block_ref(self, ref):
        self.shared_block_refs.append(ref)

    def __str__(self):
        return "metadata vaddr {self.vaddr} refs {self.refs} gen {self.generation} " \
            "flags {self.flags_str} skinny level {self.skinny_level}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.extent_flags_str, 'flags'),
        ]


class TreeBlockRef(ItemData):
    """Tree block reference

    Documentation of this item is out of scope for this module. Please refer to
    the btrfs wiki about resolving extent backreferences for more information.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key type: `TREE_BLOCK_REF_KEY` (176)

    :ivar int root: root
    """
    def __init__(self, header):
        super().__init__(header)
        self._setattr_from_key(offset_attr='root')

    def __str__(self):
        return "tree block backref root {}".format(_key_objectid_str(self.root, None))


class InlineTreeBlockRef(TreeBlockRef):
    """Identical content to :class:`TreeBlockRef`, but the backreference was
    inlined in the extent item."""
    def __init__(self, root):
        self.root = root

    def __str__(self):
        return "inline tree block backref root {}".format(_key_objectid_str(self.root, None))


class SharedBlockRef(ItemData):
    """Shared tree block reference

    Documentation of this item is out of scope for this module. Please refer to
    the btrfs wiki about resolving extent backreferences for more information.

    * Tree: `EXTENT_TREE_OBJECTID` (2)
    * Key type: `SHARED_BLOCK_REF_KEY` (182)

    :ivar int parent: parent
    """
    def __init__(self, header):
        super().__init__(header)
        self._setattr_from_key(offset_attr='parent')

    def __str__(self):
        return "shared block backref parent {}".format(self.parent)


class InlineSharedBlockRef(SharedBlockRef):
    """Identical content to :class:`SharedBlockRef`, but the backreference was
    inlined in the extent item."""
    def __init__(self, parent):
        self.parent = parent

    def __str__(self):
        return "inline shared block backref parent {}".format(self.parent)


class TimeSpec(object):
    """Object representation of struct `btrfs_timespec`.

    The :class:`TimeSpec` type of item is used embedded in other metadata items
    when a time value needs to be stored. Examples are the mtime, ctime etc
    fields in an inode item.

    It's also possible to create objects of this type manually. To do so, use
    the static :func:`~TimeSpec.from_values` helper function. (The regular
    object constructor is reserved for the code parsing metadata items from
    search queries.)

    :ivar int sec: seconds
    :ivar int nsec: nanoseconds

    Example::

        >>> my_time = btrfs.ctree.TimeSpec.from_values(1546280270, 4044945)
        >>> my_time.sec
        1546280270
        >>> my_time.nsec
        4044945
        >>> my_time.iso8601
        '2018-12-31T18:17:50.404495'
    """
    _timespec = struct.Struct('<QL')

    @staticmethod
    def from_values(sec, nsec):
        """Create a Timespec object

        :param int sec: seconds
        :param int nsec: nanoseconds
        """
        t = TimeSpec.__new__(TimeSpec)
        t.sec = sec
        t.nsec = nsec
        return t

    def __init__(self, data):
        self.sec, self.nsec = TimeSpec._timespec.unpack_from(data)

    @property
    def iso8601(self):
        """Return the timestamp as ISO8601 formatted string."""
        return datetime.datetime.utcfromtimestamp(
            float("{self.sec}.{self.nsec}".format(self=self))
        ).isoformat()

    def __str__(self):
        return "{self.sec}.{self.nsec} ({self.iso8601})".format(self=self)


class InodeItem(ItemData):
    """Object representation of struct `btrfs_inode_item`.

    The inode item stores information of a single file or directory. Not the
    name, because a file can have multiple names.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number.
    * Key type: `INODE_ITEM_KEY` (1)
    * Key offset: 0

    :ivar int objectid: The inode number. (taken from the objectid field of the
        item key).
    :ivar int generation: Generation of the filesystem when the inode was
        created.
    :ivar int transid: Generation of the filesystem when the inode was last
        changed.
    :ivar int size: File size in bytes.
    :ivar int nbytes: Allocated disk blocks for this file in bytes.
    :ivar int block_group: Only used for free space cache v1, for which it's
        the related block group virtual address.
    :ivar int nlink: Amount of hardlinks the file has.
    :ivar int uid: Numerical user id of the owner of the file.
    :ivar int gid: Numerical group id of the owner of the file.
    :ivar int mode: File permissions.
    :ivar int rdev: Major and minor device numbers for special files.
    :ivar int flags: Inode flags, see below.
    :ivar int sequence: Sequence number for NFS.
    :ivar atime: Time of last access.
    :vartype atime: :class:`~btrfs.ctree.TimeSpec`
    :ivar ctime: Time of last file metadata change. Also updated when file
        contents change.
    :vartype ctime: :class:`~btrfs.ctree.TimeSpec`
    :ivar mtime: Time of last modification to file contents.
    :vartype mtime: :class:`~btrfs.ctree.TimeSpec`
    :ivar otime: Time of file birth.
    :vartype otime: :class:`~btrfs.ctree.TimeSpec`

    The flags are an or-ed combination of one or more of the following values
    (available as attribute of this module):

    - INODE_NODATASUM
    - INODE_NODATACOW
    - INODE_READONLY
    - INODE_NOCOMPRESS
    - INODE_PREALLOC
    - INODE_SYNC
    - INODE_IMMUTABLE
    - INODE_APPEND
    - INODE_NODUMP
    - INODE_NOATIME
    - INODE_DIRSYNC
    - INODE_COMPRESS
    """
    _inode_item_parts = [
        struct.Struct('<5Q4L3Q32x'),
        TimeSpec._timespec,
        TimeSpec._timespec,
        TimeSpec._timespec,
        TimeSpec._timespec,
    ]
    _inode_item = struct.Struct('<' + ''.join([_struct_format(s)[1:]
                                               for s in _inode_item_parts]))

    def __init__(self, header, data):
        super().__init__(header)
        if header is not None:
            self._setattr_from_key(objectid_attr='objectid')
        self.generation, self.transid, self.size, self.nbytes, self.block_group, \
            self.nlink, self.uid, self.gid, self.mode, self.rdev, self.flags, self.sequence = \
            InodeItem._inode_item_parts[0].unpack_from(data)
        pos = InodeItem._inode_item_parts[0].size
        next_pos = pos + TimeSpec._timespec.size
        self.atime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec._timespec.size
        self.ctime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec._timespec.size
        self.mtime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec._timespec.size
        self.otime = TimeSpec(data[pos:next_pos])

    def __str__(self):
        result = ["inode"]
        if hasattr(self, 'objectid'):
            result.append("objectid {self.objectid}".format(self=self))
        result.append("generation {self.generation} transid {self.transid} size {self.size} "
                      "nbytes {self.nbytes} block_group {self.block_group} mode {self.mode_str} "
                      "nlink {self.nlink} uid {self.uid} gid {self.gid} rdev {self.rdev} "
                      "flags {self.flags:#x}({self.flags_str})".format(self=self))
        return " ".join(result)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.inode_flags_str, 'flags'),
            (btrfs.utils.inode_mode_str, 'mode'),
        ]


class InodeRefList(ItemData, collections.abc.MutableSequence):
    """A collection of struct `btrfs_inode_ref` indexed under a single tree
    key.

    A :class:`InodeRefList` is a list of :class:`InodeRef` objects which
    contain information about every name the inode is known under in a single
    directory. So, when we already know the inode number of a file, we can find
    in which places it has hardlinks pointing at it.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number.
    * Key type: `INODE_REF_KEY` (12)
    * Key offset: Inode number of the containing directory.

    This class is a helper that does not exist in Btrfs itself.

    Besides acting as an immutable list of :class:`InodeRef` objects, there are
    some additional attributes:

    :ivar int objectid: Inode number of the file. (taken from the objectid
        field of the item key)
    :ivar int parent_objectid: Inode number of the containing directory. (taken
        from the offset field of the item key)
    """
    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='objectid', offset_attr='parent_objectid')
        self._list = []
        pos = 0
        while pos < header.len:
            inode_ref = InodeRef(data, pos)
            self._list.append(inode_ref)
            pos += InodeRef._inode_ref.size + inode_ref.name_len

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __delitem__(self, index):
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        """Not implemented."""
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __str__(self):
        return "inode ref list objectid {self.objectid} parent_objectid {self.parent_objectid} " \
            "size {}".format(len(self), self=self)


class InodeRef(SubItem):
    """Object representation of struct `btrfs_inode_ref`.

    Also see :class:`InodeRefList`.

    :ivar int index: Directory index number in the containing directory. Refer
        to the `parent_objectid` attribute of the :class:`InodeRefList` object
        that contains this :class:`InodeRef` to find the inode number of the
        directory.
    :ivar int name_len: Amount of bytes used to store the filename.
    :ivar bytes name: Filename as bytes.
    """
    _inode_ref = struct.Struct('<QH')

    def __init__(self, data, pos):
        self.index, self.name_len = InodeRef._inode_ref.unpack_from(data, pos)
        pos += InodeRef._inode_ref.size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)

    def __str__(self):
        return "inode ref index {self.index} name {self.name_str}".format(self=self)

    def _pretty_properties():
        return [
            (btrfs.utils.embedded_text_for_str, 'name')
        ]


class InodeExtrefList(ItemData, collections.abc.MutableSequence):
    """A collection of struct `btrfs_inode_extref` indexed under a single tree
    key.

    A :class:`InodeExtrefList` is a list of :class:`InodeExtref` objects. By
    default, names under which a file is known are stored in the
    :class:`InodeRefList` of :class:`InodeRef`. However, if a file has so many
    hardlinks that that item would become bigger than a metadata page, the rest
    of the items are stored separately.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number.
    * Key type: `INODE_EXTREF_KEY` (13)
    * Key offset: :func:`~btrfs.crc32.extref_hash` of the filename.

    The :class:`InodeExtref` item is a list because multiple different
    filenames can end up having the same crc32 value.

    This class is a helper that does not exist in Btrfs itself.

    Besides acting as an immutable list of :class:`InodeExtRef` objects, there
    are some additional attributes:

    :ivar int objectid: Inode number of the file. (taken from the objectid
        field of the item key)
    :ivar int extref_hash: :func:`~btrfs.crc32.extref_hash` of the filename.
        (taken from the offset field of the item key)
    """
    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='objectid', offset_attr='extref_hash')
        self._list = []
        pos = 0
        while pos < header.len:
            inode_extref = InodeExtref(data, pos)
            self._list.append(inode_extref)
            pos += len(inode_extref)

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __delitem__(self, index):
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        """Not implemented."""
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __str__(self):
        return "inode extref list objectid {self.objectid} " \
            "hash {self.extref_hash} size {}".format(len(self), self=self)


class InodeExtref(object):
    """Object representation of struct `btrfs_inode_extref`.

    Also see :class:`InodeExtrefList`.

    :ivar int parent_objectid: Inode number of the containing directory.
    :ivar int index: Directory index number in the containing directory.
    :ivar int name_len: Amount of bytes used to store the filename.
    :ivar bytes name: Filename as bytes.
    """
    _inode_extref = struct.Struct('<QQH')

    def __init__(self, data, pos):
        self.parent_objectid, self.index, self.name_len = \
            InodeExtref._inode_extref.unpack_from(data, pos)
        pos += InodeExtref._inode_extref.size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)

    def __str__(self):
        return "inode extref parent_objectid {self.parent_objectid} index {self.index} " \
            "name {self.name_str}".format(self=self)

    def _pretty_properties():
        return [
            (btrfs.utils.embedded_text_for_str, 'name')
        ]


class DirItemList(ItemData, collections.abc.MutableSequence):
    """A collection of struct `btrfs_dir_item` indexed under a single tree key.

    A :class:`DirItemList` is a list of :class:`DirItem` objects. Based on a
    filename hash, they point to the inode item for the corresponding file.
    Since multiple different filenames can end up having the same name hash,
    this item can contain multiple :class:`DirItem` objects.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number of the directory.
    * Key type: `DIR_ITEM_KEY` (84)
    * Key offset: :func:`~btrfs.crc32.name_hash` of the filename.

    This class is a helper that does not exist in Btrfs itself.

    Besides acting as an immutable list of :class:`DirItem` objects, there are
    some additional attributes:

    :ivar int objectid: Inode number of the directory. (taken from the objectid
        field of the item key)
    :ivar int name_hash: :func:`~btrfs.crc32.name_hash` of the filename.
        (taken from the offset field of the item key)
    """
    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='objectid', offset_attr='name_hash')
        self._list = []
        pos = 0
        while pos < header.len:
            cls = {DIR_ITEM_KEY: DirItem, XATTR_ITEM_KEY: XAttrItem}
            dir_item = cls[self.key.type](data, pos)
            self._list.append(dir_item)
            pos += DirItem._dir_item.size + dir_item.name_len + dir_item.data_len

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __delitem__(self, index):
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        """Not implemented."""
        raise NotImplementedError("{} objects should not be changed.".format(type(self).__name__))

    def __str__(self):
        return "dir item list objectid {self.objectid} name_hash {self.name_hash} " \
            "size {}".format(len(self), self=self)


class XAttrItemList(DirItemList):
    """A collection of struct `btrfs_dir_item`, used to store extended
    attributes and indexed under a single tree key.

    An :class:`XAttrItemList` is a list of :class:`XAttrItem` objects, which
    contain key value pairs in the `name` and `data` fields of the dir_item
    struct.  Since multiple different keys can end up having the same name
    hash, this item can contain multiple :class:`XAttrItem` objects.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number of a file on which the xattr is set.
    * Key type: `XATTR_ITEM_KEY` (24)
    * Key offset: :func:`~btrfs.crc32.name_hash` of the key.

    This class is a helper that does not exist in Btrfs itself.

    Besides acting as an immutable list of :class:`XAttrItem` objects, there
    are some additional attributes:

    :ivar int objectid: Inode number of a file on which the xattr is set.
        (taken from the objectid field of the item key)
    :ivar int name_hash: :func:`~btrfs.crc32.name_hash` of the xattr key.
        (taken from the offset field of the item key)
    """
    def __str__(self):
        return "xattr item list objectid {self.objectid} name_hash {self.name_hash} " \
            "size {}".format(len(self), self=self)


class DirItem(SubItem):
    """Object representation of struct `btrfs_dir_item`.

    Based on the name hash of a filename, this object directly points to the
    inode item for the corresponding file. Using this mapping allows quick file
    access when the name is known, even in directories with a large amount of
    files in them.

    Also see :class:`DirItemList`.

    :ivar location: Key of the file inode item.
    :vartype location: :class:`DiskKey`
    :ivar int transid: Generation of the filesystem when this item was created.
    :ivar int data_len: *Not used*, always 0.
    :ivar int name_len: Amount of bytes used to store the filename.
    :ivar int type: File type that is represented by the inode item that is
        being referenced.
    :ivar bytes name: Filename as bytes.

    File type is one of the following values (available as attribute of this
    module):

    - FT_UNKNOWN
    - FT_REG_FILE
    - FT_DIR
    - FT_CHRDEV
    - FT_BLKDEV
    - FT_FIFO
    - FT_SOCK
    - FT_SYMLINK
    - FT_XATTR
    - FT_MAX
    """
    _dir_item_parts = [
        DiskKey._disk_key,
        struct.Struct('<QHHB')
    ]
    _dir_item = struct.Struct('<' + ''.join([_struct_format(s)[1:] for s in _dir_item_parts]))

    def __init__(self, data, pos):
        next_pos = pos + DiskKey._disk_key.size
        self.location = DiskKey(data[pos:next_pos])
        pos = next_pos
        self.transid, self.data_len, self.name_len, self.type = \
            DirItem._dir_item_parts[1].unpack_from(data, pos)
        pos += DirItem._dir_item_parts[1].size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)
        pos += self.name_len
        self.data, = struct.Struct('<{}s'.format(self.data_len)).unpack_from(data, pos)
        pos += self.data_len

    def __str__(self):
        return "dir item location {self.location} type {self.type_str} " \
            "name {self.name_str}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.dir_item_type_str, 'type'),
            (btrfs.utils.embedded_text_for_str, 'name'),
            (btrfs.utils.embedded_text_for_str, 'data'),
        ]


class XAttrItem(DirItem):
    """Object representation of struct `btrfs_dir_item`, used to store extended
    attribute information.

    This object contains a key and value for an extended attribute on a file.
    It reuses the `dir_item` data structure.

    Also see :class:`XattrItemList`.

    :ivar int transid: Generation of the filesystem when this item was created.
    :ivar int name_len: Amount of bytes used to store the key.
    :ivar int data_len: Amount of bytes used to store the value.
    :ivar bytes name: Key as bytes.
    :ivar bytes data: Value as bytes.
    """
    def __str__(self):
        return "xattr item name {self.name_str} data {self.data_str}".format(self=self)


class DirIndex(ItemData):
    """Object representation of struct `btrfs_dir_item`, but used to store
    filenames ordered on directory index.

    The :class:`DirIndex` objects list the contents of a directory in the order
    in which items were added.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number of the directory.
    * Key type: `DIR_INDEX_KEY` (96)
    * Key offset: Index in the directory.

    :ivar int objectid: Inode number of the directory. (taken from the objectid
        field of the item key)
    :ivar int index: Index in the directory. (taken from the offset field of
        the item key)
    :ivar location: Key of the file inode item.
    :vartype location: :class:`DiskKey`
    :ivar int transid: Generation of the filesystem when this item was created.
    :ivar int data_len: *Not used*, always 0.
    :ivar int name_len: Amount of bytes used to store the filename.
    :ivar int type: File type that is represented by the inode item that is
        being referenced.
    :ivar bytes name: Filename as bytes.

    File type is one of the following values (available as attribute of this
    module):

    - FT_UNKNOWN
    - FT_REG_FILE
    - FT_DIR
    - FT_CHRDEV
    - FT_BLKDEV
    - FT_FIFO
    - FT_SOCK
    - FT_SYMLINK
    - FT_XATTR
    - FT_MAX
    """
    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='objectid', offset_attr='index')
        self.location = DiskKey(data[:DiskKey._disk_key.size])
        pos = DiskKey._disk_key.size
        self.transid, self.data_len, self.name_len, self.type = \
            DirItem._dir_item_parts[1].unpack_from(data, pos)
        pos += DirItem._dir_item_parts[1].size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)

    def __str__(self):
        return "dir index objectid {self.objectid} index {self.index} " \
            "location {self.location} type {self.type_str} " \
            "name {self.name_str}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.dir_item_type_str, 'type'),
            (btrfs.utils.embedded_text_for_str, 'name'),
        ]


class RootItem(ItemData):
    """Object representation of struct `btrfs_root_item`.

    The :class:`RootItem` lives in the root tree, a.k.a. the 'tree of trees'.
    It contains information about the root metadata node of another tree.

    * Tree: `ROOT_TREE_OBJECTID` (1).
    * Key objectid: Tree ID.
    * Key type: `ROOT_ITEM_KEY` (132)
    * Key offset: Index in the directory.

    :ivar int objectid: Tree ID. (taken from the objectid field of the item
        key)
    :ivar inode: Embedded inode item. Only the flags field of it is used.
    :vartype inode: :class:`InodeItem`
    :ivar int generation: Generation of the filesystem when this root was
        created.
    :ivar int root_dirid: Objectid for the root directory in a subvolume tree
        (always 256 in that case). 0 for other trees.
    :ivar int bytenr: Virtual address of the root node of this tree.
    :ivar int byte_limit: *Not used*
    :ivar int bytes_used: *Not used*
    :ivar int last_snapshot: The generation of the filesystem when the most
        recent snapshot of a subvolume was made.
    :ivar int flags: See below.
    :ivar int refs: *Not used*, either 0 or 1.
    :ivar drop_progress: Key of the last removed item during cleanup of a
        removed subvolume.
    :vartype drop_progress: :class:`DiskKey`
    :ivar int drop_level: The tree level of the metadata node or leaf that
        contains the key from drop_progress.
    :ivar int level: The height of the tree that this root item refers to.

    The flags are an or-ed combination of one or more of the following values
    (available as attribute of this module):

    - ROOT_SUBVOL_RDONLY: The subvolume is read only.

    The following fields were introduced in Linux 3.6. Btrfs would still allow
    using the filesystem with an older kernel, but if the content of
    generation_v2 does not match generation, all new fields would be
    invalidated:

    :ivar int generation_v2: Same value as generation.
    :ivar uuid: Subvolume UUID.
    :vartype uuid: :class:`uuid.UUID`
    :ivar parent_uuid: Subvolume UUID that this subvolume is a snapshot of.
    :vartype parent_uuid: :class:`uuid.UUID`
    :ivar received_uuid: Subvolume UUID of the subvolume that this subvolume
        was duplicated from using send/receive.
    :vartype received_uuid: :class:`uuid.UUID`
    :ivar int ctransid: Generation when the tree was last modified.
    :ivar int otransid: Generation when the tree was created.
    :ivar int stransid: Generation of the filesystem from which a subvolume was
        sent. Only used if this is a received subvolume.
    :ivar int rtransid: Generation of this filesystem when the subvolume was
        received.
    :ivar ctime: Timestamp for ctransid.
    :vartype ctime: :class:`TimeSpec`
    :ivar otime: Timestamp for otransid.
    :vartype otime: :class:`TimeSpec`
    :ivar stime: Timestamp for stransid.
    :vartype stime: :class:`TimeSpec`
    :ivar rtime: Timestamp for rtransid.
    :vartype rtime: :class:`TimeSpec`
    """
    _root_item_parts = [
        InodeItem._inode_item,
        struct.Struct('<7QL'),
        DiskKey._disk_key,
        struct.Struct('<BBQ16s16s16s4Q'),
        TimeSpec._timespec,
        TimeSpec._timespec,
        TimeSpec._timespec,
        TimeSpec._timespec,
    ]
    _root_item = struct.Struct('<' + ''.join([_struct_format(s)[1:]
                                              for s in _root_item_parts]))

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='objectid')
        self.inode = InodeItem(None, data[:InodeItem._inode_item.size])
        pos = InodeItem._inode_item.size
        self.generation, self.root_dirid, self.bytenr, self.byte_limit, self.bytes_used, \
            self.last_snapshot, self.flags, self.refs = \
            RootItem._root_item_parts[1].unpack_from(data, pos)
        pos += RootItem._root_item_parts[1].size
        self.drop_progress = DiskKey(data[pos:pos+DiskKey._disk_key.size])
        pos += DiskKey._disk_key.size
        self.drop_level, self.level, self.generation_v2, uuid_bytes, parent_uuid_bytes, \
            received_uuid_bytes, self.ctransid, self.otransid, self.stransid, self.rtransid = \
            RootItem._root_item_parts[3].unpack_from(data, pos)
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.parent_uuid = uuid.UUID(bytes=parent_uuid_bytes)
        self.received_uuid = uuid.UUID(bytes=received_uuid_bytes)
        pos += RootItem._root_item_parts[3].size
        next_pos = pos + TimeSpec._timespec.size
        self.ctime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec._timespec.size
        self.otime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec._timespec.size
        self.stime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec._timespec.size
        self.rtime = TimeSpec(data[pos:next_pos])

    def __str__(self):
        return "root {self.key.objectid} uuid {self.uuid} " \
            "generation {self.generation} last_snapshot {self.last_snapshot} " \
            "flags {self.flags:#x}({self.flags_str})".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.root_item_flags_str, 'flags'),
        ]


class RootRef(ItemData):
    """Object representation of `btrfs_root_ref`.

    The :class:`RootRef` item lives in the root tree, a.k.a. the 'tree of
    trees'.  It contains information about the place where a subvolume is
    located inside another subvolume.

    * Tree: `ROOT_TREE_OBJECTID` (1).
    * Key objectid: Parent tree ID.
    * Key type: `ROOT_REF_KEY` (156)
    * Key offset: Tree ID of the subvolume.

    :ivar int parent_tree: Containing Tree ID. (taken from the objectid field of
        the item key)
    :ivar int tree: Tree ID of the subvolume. (taken from the offset field of
        the item key)
    :ivar int dirid: Inode number of the containing directory.
    :ivar int sequence: Directory index number in the containing directory.
    :ivar int name_len: Amount of bytes used to store the filename.
    :ivar bytes name: Filename as bytes.

    When combining this information with a call to the ino_lookup ioctl, we can
    quickly figure out the relative path inside the containing subvolume.

    E.g. for (259 ROOT_REF 1052) in the root tree, with dirid 20197, sequence
    65 and name baz, we can do btrfs.ioctl.ino_lookup(fd, 259, 20197). The
    result is e.g. name_bytes=b'foo/bar/', so the location inside the
    containing subvolume is foo/bar/baz.

    When doing such a thing recursively, the same output as seen in btrfs sub
    list -a can be produced.
    """
    _root_ref_item = struct.Struct('<QQH')

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='parent_tree', offset_attr='tree')
        self.dirid, self.sequence, self.name_len = RootRef._root_ref_item.unpack_from(data)
        pos = RootRef._root_ref_item.size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)

    def __str__(self):
        return "root ref parent_tree {self.parent_tree} tree {self.tree} dirid {self.dirid} " \
            "sequence {self.sequence} name {self.name_str}".format(self=self)

    def _pretty_properties():
        return [
            (btrfs.utils.embedded_text_for_str, 'name')
        ]


class FileExtentItem(ItemData):
    """Object representation of `btrfs_file_extent_item`.

    For every piece of a file, the :class:`FileExtentItem` points to the data
    extent where the actual data is stored. A :class:`FileExtentItem` does not
    have to reference a complete extent. It can also use part of it.

    * Tree: `FS_TREE_OBJECTID` (5) or any other subvolume tree.
    * Key objectid: Inode number of the file.
    * Key type: `EXTENT_DATA_KEY` (108)
    * Key offset: Logical offset in the file where the referenced data appears.

    :ivar int objectid: The inode number of the file. (taken from the objectid
        field of the item key).
    :ivar int logical_offset: Logical offset in the file where the referenced
        data appears. (taken from the offset field of the item key).
    :ivar int generation: Generation of the filesystem when this file extent
        was created.
    :ivar int ram_bytes: Upper limit on the memory needed in bytes to store the
        extent after decompression.
    :ivar int compression: Compression type, see below.

    The compression field can have one of the following values (available as
    attribute of this module):

    - COMPRESS_NONE
    - COMPRESS_ZLIB
    - COMPRESS_LZO
    - COMPRESS_ZSTD

    :ivar int encryption: *Not used* Encryption type, always 0.
    :ivar int other_encoding: *Not used*
    :ivar int type: Type of extent, see below.

    The extent type can be one of the following:

    - FILE_EXTENT_INLINE: This is an inline extent. The data is stored inside
        the metadata leaf, right after the type field.
    - FILE_EXTENT_REG: This is a regular extent.
    - FILE_EXTENT_PREALLOC: Preallocated extent (for which no actual data is
        written yet).

    If the extent type is FILE_EXTENT_INLINE, the following fields are *not*
    available:

    :ivar int disk_bytenr: Virtual address of the data extent we reference a
        range from.
    :ivar int disk_num_bytes: Size of the data extent we reference a range
        from.
    :ivar int offset: The offset inside the data extent where the data we need
        starts.
    :ivar int num_bytes: The amount of bytes to be used from that offset
        onwards.

    This means that (disk_bytenr EXTENT_ITEM disk_num_bytes) is the tree key of
    the extent item in the extent tree. Also, remember that these numbers will
    always be multiples of disk block sizes, because that's how it gets cowed.
    We don't just use 1 or 2 bytes from another extent.
    """
    _file_extent_item_parts = [
        struct.Struct('<QQBB2xB'),
        struct.Struct('<4Q'),
    ]
    _file_extent_item = struct.Struct('<' + ''.join([_struct_format(s)[1:]
                                                     for s in _file_extent_item_parts]))

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='objectid', offset_attr='logical_offset')
        self.generation, self.ram_bytes, self.compression, self.encryption, self.type = \
            FileExtentItem._file_extent_item_parts[0].unpack_from(data)
        if self.type != FILE_EXTENT_INLINE:
            pos = FileExtentItem._file_extent_item_parts[0].size
            self.disk_bytenr, self.disk_num_bytes, self.offset, self.num_bytes = \
                FileExtentItem._file_extent_item_parts[1].unpack_from(data, pos)
        else:
            self._inline_encoded_nbytes = \
                header.len - FileExtentItem._file_extent_item_parts[0].size

    def __str__(self):
        ret = ["extent data at {self.logical_offset} generation {self.generation} "
               "ram_bytes {self.ram_bytes} "
               "compression {self.compression_str} type {self.type_str}".format(self=self)]
        if self.type != FILE_EXTENT_INLINE:
            ret.append("disk_bytenr {self.disk_bytenr} disk_num_bytes {self.disk_num_bytes} "
                       "offset {self.offset} num_bytes {self.num_bytes}".format(self=self))
        else:
            ret.append("inline_encoded_nbytes {self._inline_encoded_nbytes}".format(self=self))
        return ' '.join(ret)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.compress_type_str, 'compression'),
            (btrfs.utils.file_extent_type_str, 'type'),
        ]


class FreeSpaceInfo(ItemData):
    """Object representation of struct `btrfs_free_space_info`.

    The free space tree contains a free space info item for every block group.

    * Tree: `FREE_SPACE_TREE_OBJECTID` (10).
    * Key objectid: Virtual address.
    * Key type: `FREE_SPACE_INFO_KEY` (198)
    * Key offset: Block Group length.

    :ivar int vaddr: Virtual address. (taken from the objectid field of the
        item key)
    :ivar int length: Block Group length. (taken from the offset field of the
        item key)
    :ivar int extent_count: Amount of free space extents in the Block Group.
    :ivar int flags: A flag indicating if the free space for this Block Group
        is stored as bitmap. The flag is `FREE_SPACE_USING_BITMAPS`, available
        as attribute of this module.
    """
    _free_space_info = struct.Struct('<LL')

    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='vaddr', offset_attr='length')
        self.extent_count, self.flags = FreeSpaceInfo._free_space_info.unpack(data)

    def __str__(self):
        return "free space info vaddr {self.vaddr} length {self.length_str} " \
            "extent_count {self.extent_count} flags {self.flags_str}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'length'),
            (btrfs.utils.free_space_info_flags_str, 'flags'),
        ]


class FreeSpaceExtent(ItemData):
    """Object representation for free space extent information.

    * Tree: `FREE_SPACE_TREE_OBJECTID` (10).
    * Key objectid: Virtual address of the start of the free space.
    * Key type: `FREE_SPACE_EXTENT_KEY` (199)
    * Key offset: Length of the free space.

    Note that this metadata object type does not have actual item data. All
    needed information is encoded in the item key.

    :ivar int vaddr: Virtual address of the start of the free space. (taken
        from the objectid field of the item key)
    :ivar int length: Length of the free space. (taken from the offset field of
        the item key)
    """
    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='vaddr', offset_attr='length')

    def __str__(self):
        return "free space extent vaddr {self.vaddr} length {self.length}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'length'),
        ]


class FreeSpaceBitmap(ItemData):
    """Object representation for free space bitmap information.

    * Tree: `FREE_SPACE_TREE_OBJECTID` (10).
    * Key objectid: Virtual address of the start of the free space bitmap.
    * Key type: `FREE_SPACE_BITMAP_KEY` (200)
    * Key offset: Length of the covered virtual address space.

    :ivar int vaddr: Virtual address of the start of the free space bitmap.
        (taken from the objectid field of the item key)
    :ivar int length: Length of the covered virtual address space. (taken from
        the offset field of the item key)
    :ivar bytes bitmap: The free space bitmap.
    """
    def __init__(self, header, data):
        super().__init__(header)
        self._setattr_from_key(objectid_attr='vaddr', offset_attr='length')
        self.bitmap = data

    def unpack(self, sectorsize):
        """Unpack the free space bitmap.

        :param int sectorsize: sectorsize property of the filesystem.

        :returns: A generator of :class:`btrfs.free_space_tree.FreeSpaceExtent`
            tuples.
        :rtype: Iterator[:class:`btrfs.free_space_tree.FreeSpaceExtent`]
        """
        offset = self.vaddr
        prev_bit = 0
        for cur_byte in self.bitmap:
            for bitnr in range(8):
                bit = 1 & (cur_byte >> bitnr)
                if prev_bit == 0 and bit == 1:
                    extent_start = offset
                elif prev_bit == 1 and bit == 0:
                    yield btrfs.free_space_tree.FreeSpaceExtent(
                        extent_start, offset - extent_start)
                prev_bit = bit
                offset += sectorsize
        if prev_bit == 1:
            yield btrfs.free_space_tree.FreeSpaceExtent(extent_start, offset - extent_start)

    def __str__(self):
        return "free space bitmap for vaddr {self.vaddr} length {self.length}".format(self=self)


class OrphanItem(ItemData):
    """Object representation for orphan item information from the root tree.

    * Tree: `ROOT_TREE_OBJECTID` (1).
    * Key objectid: `ORPHAN_OBJECTID` (-5).
    * Key type: `ORPHAN_ITEM_KEY` (48).
    * Key offset: objectid of the item in the root tree that is orphaned and
        needs to be cleaned up.

    :ivar int objectid: objectid of the item in the root tree that is orphaned
        and needs to be cleaned up. (taken from the offset field of the item
        key)
    """
    def __init__(self, header, _):
        super().__init__(header)
        self._setattr_from_key(offset_attr='objectid')

    def __str__(self):
        return "orphan objectid {self.objectid}".format(self=self)


class NotImplementedItem(ItemData):
    """Placeholder object for metadata item types that have not been implemented yet."""
    def __init__(self, header, data):
        super().__init__(header)
        self._data = bytearray(data)

    def __str__(self):
        return "not implemented item data ({} bytes)".format(len(self._data))


class UnknownItem(ItemData):
    """Placeholder object for metadata item types that are unrecognized."""
    def __init__(self, header, data):
        super().__init__(header)
        self._data = bytearray(data)

    def __str__(self):
        return "unknown item data ({} bytes)".format(len(self._data))


_key_type_class_map = {
    INODE_ITEM_KEY: InodeItem,
    INODE_REF_KEY: InodeRefList,
    INODE_EXTREF_KEY: InodeExtrefList,
    XATTR_ITEM_KEY: DirItemList,
    ORPHAN_ITEM_KEY: OrphanItem,
    DIR_LOG_ITEM_KEY: NotImplementedItem,
    DIR_LOG_INDEX_KEY: NotImplementedItem,
    DIR_ITEM_KEY: DirItemList,
    DIR_INDEX_KEY: DirIndex,
    EXTENT_DATA_KEY: FileExtentItem,
    EXTENT_CSUM_KEY: NotImplementedItem,
    ROOT_ITEM_KEY: RootItem,
    ROOT_REF_KEY: RootRef,
    ROOT_BACKREF_KEY: NotImplementedItem,
    EXTENT_ITEM_KEY: ExtentItem,
    METADATA_ITEM_KEY: MetaDataItem,
    TREE_BLOCK_REF_KEY: TreeBlockRef,
    EXTENT_DATA_REF_KEY: ExtentDataRef,
    SHARED_BLOCK_REF_KEY: SharedBlockRef,
    SHARED_DATA_REF_KEY: SharedDataRef,
    BLOCK_GROUP_ITEM_KEY: BlockGroupItem,
    FREE_SPACE_INFO_KEY: FreeSpaceInfo,
    FREE_SPACE_EXTENT_KEY: FreeSpaceExtent,
    FREE_SPACE_BITMAP_KEY: FreeSpaceBitmap,
    DEV_EXTENT_KEY: DevExtent,
    DEV_ITEM_KEY: DevItem,
    CHUNK_ITEM_KEY: Chunk,
    QGROUP_STATUS_KEY: NotImplementedItem,
    QGROUP_INFO_KEY: NotImplementedItem,
    QGROUP_LIMIT_KEY: NotImplementedItem,
    DEV_REPLACE_KEY: NotImplementedItem,
    UUID_KEY_SUBVOL: NotImplementedItem,
    UUID_KEY_RECEIVED_SUBVOL: NotImplementedItem,
    STRING_ITEM_KEY: NotImplementedItem,
}


def classify(header, data):
    """
    Convenience function to automatically convert an item header and data into
    one of the object types in this module.

    :param header: Search header.
    :type header: :class:`btrfs.ioctl.SearchHeader`
    :param bytes data: Item data.
    :returns: Object representing the metadata item.
    :rtype: Subclass of :class:`ItemData`

    Example::

        >>> with btrfs.FileSystem('/') as fs:
        ...     chunk_tree_objects = btrfs.ioctl.search_v2(fs.fd, 3)
        ...     btrfs.utils.pretty_print(
        ...         (btrfs.ctree.classify(header, data)
        ...          for header, data in chunk_tree_objects)
        ...     )

    The search function returns a generator, which we name chunk_tree_objects.
    The pretty printer can handle any iterable, so the above fragment will, in
    a 'streaming' way, dump the chunk tree on the screen.
    """
    if header.type == PERSISTENT_ITEM_KEY:
        if header.objectid == DEV_STATS_OBJECTID:
            return NotImplementedItem(header, data)
        return UnknownItem(header, data)

    if header.type == TEMPORARY_ITEM_KEY:
        if header.objectid == BALANCE_OBJECTID:
            return NotImplementedItem(header, data)
        return UnknownItem(header, data)

    return _key_type_class_map.get(header.type, UnknownItem)(header, data)
