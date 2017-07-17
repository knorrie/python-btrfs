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

import collections.abc
import copy
import os
import struct
import uuid

ULLONG_MAX = (1 << 64) - 1
ULONG_MAX = (1 << 32) - 1


def ULL(n):
    return n & ULLONG_MAX


ROOT_TREE_OBJECTID = 1
EXTENT_TREE_OBJECTID = 2
CHUNK_TREE_OBJECTID = 3
DEV_TREE_OBJECTID = 4
FS_TREE_OBJECTID = 5
ROOT_TREE_DIR_OBJECTID = 6
CSUM_TREE_OBJECTID = 7
QUOTA_TREE_OBJECTID = 8
UUID_TREE_OBJECTID = 9
FREE_SPACE_TREE_OBJECTID = 10

DEV_STATS_OBJECTID = 0
BALANCE_OBJECTID = ULL(-4)
ORPHAN_OBJECTID = ULL(-5)
TREE_LOG_OBJECTID = ULL(-6)
TREE_LOG_FIXUP_OBJECTID = ULL(-7)
TREE_RELOC_OBJECTID = ULL(-8)
DATA_RELOC_TREE_OBJECTID = ULL(-9)
EXTENT_CSUM_OBJECTID = ULL(-10)
FREE_SPACE_OBJECTID = ULL(-11)
FREE_INO_OBJECTID = ULL(-12)
MULTIPLE_OBJECTIDS = ULL(-255)

FIRST_FREE_OBJECTID = 256
LAST_FREE_OBJECTID = ULL(-256)
FIRST_CHUNK_TREE_OBJECTID = 256

DEV_ITEMS_OBJECTID = 1


INODE_ITEM_KEY = 1
INODE_REF_KEY = 12
INODE_EXTREF_KEY = 13
XATTR_ITEM_KEY = 24
ORPHAN_ITEM_KEY = 48
DIR_LOG_ITEM_KEY = 60
DIR_LOG_INDEX_KEY = 72
DIR_ITEM_KEY = 84
DIR_INDEX_KEY = 96
EXTENT_DATA_KEY = 108
CSUM_ITEM_KEY = 120
EXTENT_CSUM_KEY = 128
ROOT_ITEM_KEY = 132
ROOT_BACKREF_KEY = 144
ROOT_REF_KEY = 156
EXTENT_ITEM_KEY = 168
METADATA_ITEM_KEY = 169
TREE_BLOCK_REF_KEY = 176
EXTENT_DATA_REF_KEY = 178
SHARED_BLOCK_REF_KEY = 182
SHARED_DATA_REF_KEY = 184
BLOCK_GROUP_ITEM_KEY = 192
FREE_SPACE_INFO_KEY = 198
FREE_SPACE_EXTENT_KEY = 199
FREE_SPACE_BITMAP_KEY = 200
DEV_EXTENT_KEY = 204
DEV_ITEM_KEY = 216
CHUNK_ITEM_KEY = 228
QGROUP_STATUS_KEY = 240
QGROUP_INFO_KEY = 242
QGROUP_LIMIT_KEY = 244
QGROUP_RELATION_KEY = 246
BALANCE_ITEM_KEY = 248
DEV_STATS_KEY = 249
DEV_REPLACE_KEY = 250
UUID_KEY_SUBVOL = 251
UUID_KEY_RECEIVED_SUBVOL = 252
STRING_ITEM_KEY = 253

BLOCK_GROUP_SINGLE = 0
BLOCK_GROUP_DATA = 1 << 0
BLOCK_GROUP_SYSTEM = 1 << 1
BLOCK_GROUP_METADATA = 1 << 2
BLOCK_GROUP_RAID0 = 1 << 3
BLOCK_GROUP_RAID1 = 1 << 4
BLOCK_GROUP_DUP = 1 << 5
BLOCK_GROUP_RAID10 = 1 << 6
BLOCK_GROUP_RAID5 = 1 << 7
BLOCK_GROUP_RAID6 = 1 << 8

BLOCK_GROUP_TYPE_MASK = (
    BLOCK_GROUP_DATA |
    BLOCK_GROUP_SYSTEM |
    BLOCK_GROUP_METADATA
)

BLOCK_GROUP_PROFILE_MASK = (
    BLOCK_GROUP_RAID0 |
    BLOCK_GROUP_RAID1 |
    BLOCK_GROUP_RAID5 |
    BLOCK_GROUP_RAID6 |
    BLOCK_GROUP_DUP |
    BLOCK_GROUP_RAID10
)

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
}

_balance_args_profiles_str_map = {
    BLOCK_GROUP_RAID0: 'RAID0',
    BLOCK_GROUP_RAID1: 'RAID1',
    BLOCK_GROUP_DUP: 'DUP',
    BLOCK_GROUP_RAID10: 'RAID10',
    BLOCK_GROUP_RAID5: 'RAID5',
    BLOCK_GROUP_RAID6: 'RAID6',
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

_inode_flags_str_map = {
    INODE_NODATASUM: 'NODATASUM',
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

_compress_type_str_map = {
    COMPRESS_NONE: 'none',
    COMPRESS_ZLIB: 'zlib',
    COMPRESS_LZO: 'lzo',
}

FILE_EXTENT_INLINE = 0
FILE_EXTENT_REG = 1
FILE_EXTENT_PREALLOC = 2

_file_extent_type_str_map = {
    FILE_EXTENT_INLINE: 'inline',
    FILE_EXTENT_REG: 'regular',
    FILE_EXTENT_PREALLOC: 'prealloc',
}


def qgroup_level(objectid):
    return objectid >> QGROUP_LEVEL_SHIFT


def qgroup_subvid(objectid):
    return objectid & ((1 << QGROUP_LEVEL_SHIFT) - 1)


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


def key_objectid_str(objectid, _type):
    if _type == DEV_EXTENT_KEY:
        return str(objectid)
    if _type == QGROUP_RELATION_KEY:
        return "{}/{}".format(qgroup_level(objectid), qgroup_subvid(objectid))
    if _type == UUID_KEY_SUBVOL or _type == UUID_KEY_RECEIVED_SUBVOL:
        return "0x{:0>16x}".format(objectid)

    if objectid == ROOT_TREE_OBJECTID and _type == DEV_ITEM_KEY:
        return 'DEV_ITEMS'
    if objectid == DEV_STATS_OBJECTID and _type == DEV_STATS_KEY:
        return 'DEV_STATS'
    if objectid == FIRST_CHUNK_TREE_OBJECTID and _type == CHUNK_ITEM_KEY:
        return 'FIRST_CHUNK_TREE'
    if objectid == ULLONG_MAX:
        return '-1'

    return _key_objectid_str_map.get(objectid, str(objectid))


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
    CSUM_ITEM_KEY: 'CSUM_ITEM',
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
    BALANCE_ITEM_KEY: 'BALANCE_ITEM',
    DEV_STATS_KEY: 'DEV_STATS',
    DEV_REPLACE_KEY: 'DEV_REPLACE',
    UUID_KEY_SUBVOL: 'UUID_SUBVOL',
    UUID_KEY_RECEIVED_SUBVOL: 'RECEIVED_SUBVOL',
    STRING_ITEM_KEY: 'STRING_ITEM',
}


def key_type_str(_type):
    return _key_type_str_map.get(_type, str(_type))


def key_offset_str(offset, _type):
    if _type == QGROUP_RELATION_KEY or _type == QGROUP_INFO_KEY or _type == QGROUP_LIMIT_KEY:
        return "{}/{}".format(qgroup_level(offset), qgroup_subvid(offset))
    if _type == UUID_KEY_SUBVOL or _type == UUID_KEY_RECEIVED_SUBVOL:
        return "0x{:0>16x}".format(offset)
    if offset == ULLONG_MAX:
        return '-1'

    return str(offset)


import btrfs.ioctl  # noqa
import btrfs.free_space_tree  # noqa


class Key(object):
    def __init__(self, objectid, _type, offset):
        self._objectid = objectid
        self._type = _type
        self._offset = offset
        self._pack()

    @property
    def objectid(self):
        return self._objectid

    @objectid.setter
    def objectid(self, _objectid):
        self._objectid = _objectid
        self._pack()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, _type):
        self._type = _type
        self._pack()

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, _offset):
        self._offset = _offset
        self._pack()

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, _key):
        self._key = _key
        self._unpack()

    def _pack(self):
        self._key = (self.objectid << 72) + (self._type << 64) + self.offset

    def _unpack(self):
        self._objectid = self._key >> 72
        self._type = (self._key & ((1 << 72) - 1)) >> 64
        self._offset = (self._key & ((1 << 64) - 1))

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

    def __str__(self):
        return "({} {} {})".format(
            key_objectid_str(self._objectid, self._type),
            key_type_str(self._type),
            key_offset_str(self._offset, self._type),
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
    disk_key = struct.Struct('<QBQ')

    def __init__(self, data):
        super(DiskKey, self).__init__(*DiskKey.disk_key.unpack_from(data))


class FileSystem(object):
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY)
        _fs_info = self.fs_info()
        self.fsid = _fs_info.fsid
        self.nodesize = _fs_info.nodesize
        self.sectorsize = _fs_info.sectorsize

    def fs_info(self):
        return btrfs.ioctl.fs_info(self.fd)

    def dev_info(self, devid):
        return btrfs.ioctl.dev_info(self.fd, devid)

    def dev_stats(self, devid, reset=False):
        return btrfs.ioctl.dev_stats(self.fd, devid, reset)

    def space_info(self):
        return btrfs.ioctl.space_info(self.fd)

    def devices(self, min_devid=1, max_devid=ULLONG_MAX):
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(DEV_ITEMS_OBJECTID, DEV_ITEM_KEY, min_devid)
        max_key = Key(DEV_ITEMS_OBJECTID, DEV_ITEM_KEY, max_devid)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            yield DevItem(header, data)

    def chunks(self, min_vaddr=0, max_vaddr=ULLONG_MAX, nr_items=ULONG_MAX):
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, min_vaddr)
        max_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, max_vaddr)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key,
                                                  nr_items=nr_items):
            yield Chunk(header, data)

    def dev_extents(self, min_devid=1, max_devid=ULLONG_MAX):
        tree = DEV_TREE_OBJECTID
        min_key = btrfs.ctree.Key(min_devid, 0, 0)
        max_key = btrfs.ctree.Key(max_devid, 255, ULLONG_MAX)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            yield DevExtent(header, data)

    def block_group(self, vaddr, length=None):
        tree = EXTENT_TREE_OBJECTID
        min_offset = length if length is not None else 0
        max_offset = length if length is not None else ULLONG_MAX
        min_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, min_offset)
        max_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, max_offset)
        block_groups = [BlockGroupItem(header, data)
                        for header, data in
                        btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key, nr_items=1)]
        return block_groups[0]

    def extents(self, min_vaddr=0, max_vaddr=ULLONG_MAX,
                load_data_refs=False, load_metadata_refs=False):
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
                    extent.append_extent_data_ref(ExtentDataRef(header, data))
            elif header.type == SHARED_DATA_REF_KEY:
                if load_data_refs:
                    extent.append_shared_data_ref(SharedDataRef(header, data))
            elif header.type == TREE_BLOCK_REF_KEY:
                if load_metadata_refs:
                    extent.append_tree_block_ref(TreeBlockRef(header))
            elif header.type == SHARED_BLOCK_REF_KEY:
                if load_metadata_refs:
                    extent.append_shared_block_ref(SharedBlockRef(header))
            elif header.type != BLOCK_GROUP_ITEM_KEY:
                raise Exception("BUG: unexpected object {}".format(
                    Key(header.objectid, header.type, header.offset)))

        if extent is not None:
            yield extent

    def top_level(self):
        return list(self.subvolumes(min_id=FS_TREE_OBJECTID, max_id=FS_TREE_OBJECTID))[0]

    def subvolumes(self, min_id=FIRST_FREE_OBJECTID, max_id=LAST_FREE_OBJECTID):
        tree = ROOT_TREE_OBJECTID
        if min_id == max_id:
            min_type = ROOT_ITEM_KEY
            max_type = ROOT_ITEM_KEY
        else:
            min_type = 0
            max_type = 255
        min_key = Key(min_id, min_type, 0)
        max_key = Key(max_id, max_type, ULLONG_MAX)
        cur_header = None
        cur_data = None
        for next_header, next_data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            if next_header.type != ROOT_ITEM_KEY:
                continue
            if cur_header is not None and next_header.objectid > cur_header.objectid:
                yield RootItem(cur_header, cur_data)
            cur_header = next_header
            cur_data = next_data

        if cur_header is not None:
            yield RootItem(cur_header, cur_data)

    def orphan_subvol_ids(self):
        tree = ROOT_TREE_OBJECTID
        min_key = Key(ORPHAN_OBJECTID, ORPHAN_ITEM_KEY, 0)
        max_key = Key(ORPHAN_OBJECTID, ORPHAN_ITEM_KEY, ULLONG_MAX)
        subvol_ids = [header.offset
                      for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key)]
        return subvol_ids

    def free_space_extents(self, min_vaddr=0, max_vaddr=ULLONG_MAX):
        tree = FREE_SPACE_TREE_OBJECTID
        min_key = Key(min_vaddr, 0, 0)
        max_key = Key(max_vaddr, 255, ULLONG_MAX)
        for header, data in btrfs.ioctl.search_v2(self.fd, tree, min_key, max_key):
            if header.type == FREE_SPACE_EXTENT_KEY:
                yield btrfs.free_space_tree.FreeSpaceExtent(header.objectid, header.offset)
            elif header.type == FREE_SPACE_BITMAP_KEY:
                yield from btrfs.free_space_tree.unpack_bitmap(
                    header.objectid, self.sectorsize, data)
            elif header.type != FREE_SPACE_INFO_KEY:
                raise Exception("BUG: unexpected object {}".format(
                    Key(header.objectid, header.type, header.offset)))


class ItemData(object):
    def __init__(self, header):
        if isinstance(header, btrfs.ioctl.SearchHeader):
            self.key = Key(header.objectid, header.type, header.offset)
        elif header is not None:
            raise TypeError("Not a SearchHeader: {}".format(header))

    def __lt__(self, other):
        return self.key < other.key


class DevItem(ItemData):
    dev_item = struct.Struct('<3Q3L3QL2B16s16s')

    def __init__(self, header, data):
        super().__init__(header)
        self.devid, self.total_bytes, self.bytes_used, self.io_align, self.io_width, \
            self.sector_size, self.type, self.generation, self.start_offset, self.dev_group, \
            self.seek_speed, self.bandwidth, uuid_bytes, fsid_bytes = \
            DevItem.dev_item.unpack(data)
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.fsid = uuid.UUID(bytes=fsid_bytes)

    def __str__(self):
        return "dev item devid {self.devid} total bytes {self.total_bytes} " \
            "bytes used {self.bytes_used}".format(self=self)


class Chunk(ItemData):
    chunk = struct.Struct('<4Q3L2H')

    def __init__(self, header, data):
        super().__init__(header)
        self.vaddr = header.offset
        self.length, self.owner, self.stripe_len, self.type, self.io_align, \
            self.io_width, self.sector_size, self.num_stripes, self.sub_stripes = \
            Chunk.chunk.unpack_from(data)
        self.stripes = []
        pos = Chunk.chunk.size
        for i in range(self.num_stripes):
            next_pos = pos + Stripe.stripe.size
            self.stripes.append(Stripe(self, data[pos:next_pos]))
            pos = next_pos

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.type, _block_group_flags_str_map)

    def __str__(self):
        return "chunk vaddr {self.vaddr} type {self.flags_str} length {self.length} " \
            "num_stripes {self.num_stripes}".format(self=self)


class Stripe(object):
    stripe = struct.Struct('<2Q16s')

    def __init__(self, chunk, data):
        self.chunk = chunk
        self.devid, self.offset, uuid_bytes = Stripe.stripe.unpack(data)
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "stripe devid {self.devid} offset {self.offset}".format(self=self)


class DevExtent(ItemData):
    dev_extent = struct.Struct('<4Q16s')

    def __init__(self, header, data):
        super().__init__(header)
        self.devid = header.objectid
        self.paddr = header.offset
        self.chunk_tree, self.chunk_objectid, self.chunk_offset, self.length, uuid_bytes = \
            DevExtent.dev_extent.unpack(data)
        self.vaddr = self.chunk_offset
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "dev extent devid {self.devid} paddr {self.paddr} length {self.length} " \
            "chunk {self.chunk_offset}".format(self=self)


class BlockGroupItem(ItemData):
    block_group_item = struct.Struct('<3Q')

    def __init__(self, header, data):
        super().__init__(header)
        self.vaddr = header.objectid
        self.length = header.offset
        self.used, self.chunk_objectid, self.flags = \
            BlockGroupItem.block_group_item.unpack(data)

    @property
    def used_pct(self):
        return int(round((self.used * 100) / self.length))

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.flags, _block_group_flags_str_map)

    def __str__(self):
        return "block group vaddr {self.vaddr} length {self.length} " \
            "flags {self.flags_str} used {self.used} used_pct {self.used_pct}".format(self=self)


class ExtentItem(ItemData):
    extent_item = struct.Struct('<3Q')
    extent_inline_ref = struct.Struct('<BQ')

    def __init__(self, header, data, load_data_refs=False, load_metadata_refs=False):
        super().__init__(header)
        pos = 0
        self.vaddr = header.objectid
        self.length = header.offset
        self.refs, self.generation, self.flags = ExtentItem.extent_item.unpack_from(data, pos)
        pos += ExtentItem.extent_item.size
        if self.flags == EXTENT_FLAG_DATA and load_data_refs:
            self.extent_data_refs = []
            self.shared_data_refs = []
            while pos < len(data):
                inline_ref_type, inline_ref_offset = \
                    ExtentItem.extent_inline_ref.unpack_from(data, pos)
                if inline_ref_type == EXTENT_DATA_REF_KEY:
                    pos += 1
                    next_pos = pos + InlineExtentDataRef.inline_extent_data_ref.size
                    self.extent_data_refs.append(InlineExtentDataRef(data[pos:next_pos]))
                    pos = next_pos
                elif inline_ref_type == SHARED_DATA_REF_KEY:
                    pos += 1
                    next_pos = pos + InlineSharedDataRef.inline_shared_data_ref.size
                    self.shared_data_refs.append(InlineSharedDataRef(data[pos:next_pos]))
                    pos = next_pos
        elif self.flags & EXTENT_FLAG_TREE_BLOCK and load_metadata_refs:
            next_pos = pos + TreeBlockInfo.tree_block_info.size
            self.tree_block_info = TreeBlockInfo(data[pos:next_pos])
            pos = next_pos
            self.tree_block_refs = []
            self.shared_block_refs = []
            while pos < len(data):
                inline_ref_type, inline_ref_offset = \
                    ExtentItem.extent_inline_ref.unpack_from(data, pos)
                if inline_ref_type == TREE_BLOCK_REF_KEY:
                    self.tree_block_refs.append(InlineTreeBlockRef(inline_ref_offset))
                elif inline_ref_type == SHARED_BLOCK_REF_KEY:
                    self.shared_block_refs.append(InlineSharedBlockRef(inline_ref_offset))
                else:
                    raise Exception("BUG: expected inline TREE_BLOCK_REF or SHARED_BLOCK_REF_KEY "
                                    "but got inline_ref_type {}".format(inline_ref_type))
                pos += ExtentItem.extent_inline_ref.size

    def append_extent_data_ref(self, ref):
        self.extent_data_refs.append(ref)

    def append_shared_data_ref(self, ref):
        self.shared_data_refs.append(ref)

    def append_tree_block_ref(self, ref):
        self.tree_block_refs.append(ref)

    def append_shared_block_ref(self, ref):
        self.shared_block_refs.append(ref)

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.flags, _extent_flags_str_map)

    def __str__(self):
        return "extent vaddr {self.vaddr} length {self.length} refs {self.refs} " \
            "gen {self.generation} flags {self.flags_str}".format(self=self)


class ExtentDataRef(ItemData):
    extent_data_ref = struct.Struct('<3QL')

    def __init__(self, header, data):
        super().__init__(header)
        self.root, self.objectid, self.offset, self.count = \
            ExtentDataRef.extent_data_ref.unpack(data)

    def __str__(self):
        return "extent data backref root {self.root} objectid {self.objectid} " \
            "offset {self.offset} count {self.count}".format(self=self)


class InlineExtentDataRef(ExtentDataRef):
    inline_extent_data_ref = ExtentDataRef.extent_data_ref

    def __init__(self, data):
        self.root, self.objectid, self.offset, self.count = \
            InlineExtentDataRef.inline_extent_data_ref.unpack(data)

    def __str__(self):
        return "inline extent data backref root {self.root} objectid {self.objectid} " \
            "offset {self.offset} count {self.count}".format(self=self)


class SharedDataRef(ItemData):
    shared_data_ref = struct.Struct('<L')

    def __init__(self, header, data):
        super().__init__(header)
        self.parent = header.offset
        self.count, = SharedDataRef.shared_data_ref.unpack(data)

    def __str__(self):
        return "shared data backref parent {self.parent} count {self.count}".format(self=self)


class InlineSharedDataRef(SharedDataRef):
    inline_shared_data_ref = struct.Struct('<QL')

    def __init__(self, data):
        self.parent, self.count = InlineSharedDataRef.inline_shared_data_ref.unpack(data)

    def __str__(self):
        return "inline shared data backref parent {self.parent} " \
            "count {self.count}".format(self=self)


class TreeBlockInfo(object):
    tree_block_info = struct.Struct('<QBQB')

    def __init__(self, data):
        tb_objectid, tb_type, tb_offset, self.level = \
            TreeBlockInfo.tree_block_info.unpack(data)
        self.key = Key(tb_objectid, tb_type, tb_offset)

    def __str__(self):
        return "tree block key {self.key} level {self.level}".format(self=self)


class MetaDataItem(ItemData):
    def __init__(self, header, data, load_refs=False):
        super().__init__(header)
        self.vaddr = header.objectid
        self.skinny_level = header.offset
        self.refs, self.generation, self.flags = ExtentItem.extent_item.unpack_from(data)
        if load_refs:
            self._load_refs(data[ExtentItem.extent_item.size:])

    def _load_refs(self, data):
        pos = 0
        self.tree_block_refs = []
        self.shared_block_refs = []
        while pos < len(data):
            inline_ref_type, inline_ref_offset = \
                ExtentItem.extent_inline_ref.unpack_from(data, pos)
            if inline_ref_type == TREE_BLOCK_REF_KEY:
                self.tree_block_refs.append(InlineTreeBlockRef(inline_ref_offset))
            elif inline_ref_type == SHARED_BLOCK_REF_KEY:
                self.shared_block_refs.append(InlineSharedBlockRef(inline_ref_offset))
            else:
                raise Exception("BUG: expected inline TREE_BLOCK_REF or SHARED_BLOCK_REF_KEY "
                                "in METADATA_ITEM {}, but got inline_ref_type {}"
                                "".format(self.key, inline_ref_type))
            pos += ExtentItem.extent_inline_ref.size

    def append_tree_block_ref(self, ref):
        self.tree_block_refs.append(ref)

    def append_shared_block_ref(self, ref):
        self.shared_block_refs.append(ref)

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.flags, _extent_flags_str_map)

    def __str__(self):
        return "metadata vaddr {self.vaddr} refs {self.refs} gen {self.generation} " \
            "flags {self.flags_str} skinny level {self.skinny_level}".format(self=self)


class TreeBlockRef(ItemData):
    def __init__(self, header):
        super().__init__(header)
        self.root = header.offset

    def __str__(self):
        return "tree block backref root {}".format(key_objectid_str(self.root, None))


class InlineTreeBlockRef(TreeBlockRef):
    def __init__(self, root):
        self.root = root

    def __str__(self):
        return "inline tree block backref root {}".format(key_objectid_str(self.root, None))


class SharedBlockRef(ItemData):
    def __init__(self, header):
        super().__init__(header)
        self.parent = header.offset

    def __str__(self):
        return "shared block backref parent {}".format(self.parent)


class InlineSharedBlockRef(SharedBlockRef):
    def __init__(self, parent):
        self.parent = parent

    def __str__(self):
        return "inline shared block backref parent {}".format(self.parent)


class TimeSpec(object):
    timespec = struct.Struct('<QL')

    def __init__(self, data):
        self.sec, self.nsec = TimeSpec.timespec.unpack_from(data)

    def __str__(self):
        return "{self.sec}.{self.nsec}".format(self=self)


class InodeItem(ItemData):
    _inode_item = [
        struct.Struct('<5Q4L3Q32x'),
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
    ]
    inode_item = struct.Struct('<' + ''.join([s.format[1:].decode() for s in _inode_item]))

    def __init__(self, header, data):
        super().__init__(header)
        self.generation, self.transid, self.size, self.nbytes, self.block_group, \
            self.nlink, self.uid, self.gid, self.mode, self.rdev, self.flags, self.sequence = \
            InodeItem._inode_item[0].unpack_from(data)
        pos = InodeItem._inode_item[0].size
        next_pos = pos + TimeSpec.timespec.size
        self.atime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec.timespec.size
        self.ctime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec.timespec.size
        self.mtime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec.timespec.size
        self.otime = TimeSpec(data[pos:next_pos])

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.flags, _inode_flags_str_map)

    def __str__(self):
        return "inode generation {self.generation} transid {self.transid} size {self.size} " \
            "nbytes {self.nbytes} block_group {self.block_group} mode {self.mode:05o} " \
            "nlink {self.nlink} uid {self.uid} gid {self.gid} rdev {self.rdev} " \
            "flags {self.flags:#x}({self.flags_str})".format(self=self)


class InodeRefList(ItemData, collections.abc.MutableSequence):
    def __init__(self, header, data):
        super().__init__(header)
        self._list = []
        pos = 0
        while pos < header.len:
            inode_ref = InodeRef(data, pos)
            self._list.append(inode_ref)
            pos += len(inode_ref)

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value

    def __delitem__(self, index):
        del self._list[index]

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        self._list.insert(index, value)

    def __str__(self):
        return "inode ref list size {}".format(len(self))


class InodeRef(object):
    inode_ref = struct.Struct('<QH')

    def __init__(self, data, pos):
        self.index, self.name_len = InodeRef.inode_ref.unpack_from(data, pos)
        pos += InodeRef.inode_ref.size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)
        self._len = InodeRef.inode_ref.size + self.name_len

    @property
    def name_str(self):
        return btrfs.utils.embedded_text_for_str(self.name)

    def __len__(self):
        return self._len

    def __str__(self):
        return "inode ref index {self.index} name {self.name_str}".format(self=self)


class InodeExtrefList(ItemData, collections.abc.MutableSequence):
    def __init__(self, header, data):
        super().__init__(header)
        self._list = []
        pos = 0
        while pos < header.len:
            inode_extref = InodeExtref(data, pos)
            self._list.append(inode_extref)
            pos += len(inode_extref)

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value

    def __delitem__(self, index):
        del self._list[index]

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        self._list.insert(index, value)

    def __str__(self):
        return "inode extref list hash {self.key.offset} size {}".format(len(self), self=self)


class InodeExtref(object):
    inode_extref = struct.Struct('<QQH')

    def __init__(self, data, pos):
        self.parent_objectid, self.index, self.name_len = \
            InodeExtref.inode_extref.unpack_from(data, pos)
        pos += InodeExtref.inode_extref.size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)
        self._len = InodeExtref.inode_extref.size + self.name_len

    @property
    def name_str(self):
        return btrfs.utils.embedded_text_for_str(self.name)

    def __len__(self):
        return self._len

    def __str__(self):
        return "inode extref parent_objectid {self.parent_objectid} index {self.index} " \
            "name {self.name_str}".format(self=self)


class DirItemList(ItemData, collections.abc.MutableSequence):
    def __init__(self, header, data):
        super().__init__(header)
        self._list = []
        pos = 0
        while pos < header.len:
            cls = {DIR_ITEM_KEY: DirItem, XATTR_ITEM_KEY: XAttrItem}
            dir_item = cls[self.key.type](data, pos)
            self._list.append(dir_item)
            pos += len(dir_item)

    def __getitem__(self, index):
        return self._list[index]

    def __setitem__(self, index, value):
        self._list[index] = value

    def __delitem__(self, index):
        del self._list[index]

    def __len__(self):
        return len(self._list)

    def insert(self, index, value):
        self._list.insert(index, value)

    def __str__(self):
        return "dir item list hash {self.key.offset} size {}".format(len(self), self=self)


class XAttrItemList(DirItemList):
    def __str__(self):
        return "xattr item list hash {self.key.offset} size {}".format(len(self), self=self)


class DirItem(object):
    _dir_item = [
        DiskKey.disk_key,
        struct.Struct('<QHHB')
    ]
    dir_item = struct.Struct('<' + ''.join([s.format[1:].decode() for s in _dir_item]))

    def __init__(self, data, pos):
        next_pos = pos + DiskKey.disk_key.size
        self.location = DiskKey(data[pos:next_pos])
        pos = next_pos
        self.transid, self.data_len, self.name_len, self.type = \
            DirItem._dir_item[1].unpack_from(data, pos)
        pos += DirItem._dir_item[1].size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)
        pos += self.name_len
        self.data, = struct.Struct('<{}s'.format(self.data_len)).unpack_from(data, pos)
        pos += self.data_len
        self._len = DirItem.dir_item.size + self.name_len + self.data_len

    @property
    def type_str(self):
        return _dir_item_type_str_map[self.type]

    @property
    def name_str(self):
        return btrfs.utils.embedded_text_for_str(self.name)

    @property
    def data_str(self):
        return btrfs.utils.embedded_text_for_str(self.data)

    def __len__(self):
        return self._len

    def __str__(self):
        return "dir item location {self.location} type {self.type_str} " \
            "name {self.name_str}".format(self=self)


class XAttrItem(DirItem):
    def __str__(self):
        return "xattr item name {self.name_str} data {self.data_str}".format(self=self)


class DirIndex(ItemData):
    def __init__(self, header, data):
        super().__init__(header)
        self.location = DiskKey(data[:DiskKey.disk_key.size])
        pos = DiskKey.disk_key.size
        self.transid, self.data_len, self.name_len, self.type = \
            DirItem._dir_item[1].unpack_from(data, pos)
        pos += DirItem._dir_item[1].size
        self.name, = struct.Struct('<{}s'.format(self.name_len)).unpack_from(data, pos)

    @property
    def type_str(self):
        return _dir_item_type_str_map[self.type]

    @property
    def name_str(self):
        return btrfs.utils.embedded_text_for_str(self.name)

    def __str__(self):
        return "dir index {self.key.offset} location {self.location} type {self.type_str} " \
            "name {self.name_str}".format(self=self)


class RootItem(ItemData):
    _root_item = [
        InodeItem.inode_item,
        struct.Struct('<7QL'),
        DiskKey.disk_key,
        struct.Struct('<BBQ16s16s16s4Q'),
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
    ]
    root_item = struct.Struct('<' + ''.join([s.format[1:].decode() for s in _root_item]))

    def __init__(self, header, data):
        super().__init__(header)
        self.inode = InodeItem(None, data[:InodeItem.inode_item.size])
        pos = InodeItem.inode_item.size
        self.generation, self.dirid, self.bytenr, self.byte_limit, self.bytes_used, \
            self.last_snapshot, self.flags, self.refs = \
            RootItem._root_item[1].unpack_from(data, pos)
        pos += RootItem._root_item[1].size
        self.drop_progress = DiskKey(data[pos:pos+DiskKey.disk_key.size])
        pos += DiskKey.disk_key.size
        self.drop_level, self.level, self.generation_v2, uuid_bytes, parent_uuid_bytes, \
            received_uuid_bytes, self.ctransid, self.otransid, self.stransid, self.rtransid = \
            RootItem._root_item[3].unpack_from(data, pos)
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.parent_uuid = uuid.UUID(bytes=parent_uuid_bytes)
        self.received_uuid = uuid.UUID(bytes=received_uuid_bytes)
        pos += RootItem._root_item[3].size
        next_pos = pos + TimeSpec.timespec.size
        self.ctime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec.timespec.size
        self.otime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec.timespec.size
        self.stime = TimeSpec(data[pos:next_pos])
        pos, next_pos = next_pos, next_pos + TimeSpec.timespec.size
        self.rtime = TimeSpec(data[pos:next_pos])

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.flags, _root_flags_str_map)

    def __str__(self):
        return "root {self.key.objectid} uuid {self.uuid} dirid {self.dirid} " \
            "gen {self.generation} last_snapshot {self.last_snapshot} " \
            "flags {self.flags:#x}({self.flags_str})".format(self=self)


class FileExtentItem(ItemData):
    _file_extent_item = [
        struct.Struct('<QQBB2xB'),
        struct.Struct('<4Q'),
    ]
    file_extent_item = struct.Struct('<' + ''.join([s.format[1:].decode()
                                                    for s in _file_extent_item]))

    def __init__(self, header, data):
        super().__init__(header)
        self.logical_offset = header.offset
        self.generation, self.ram_bytes, self.compression, self.encryption, self.type = \
            FileExtentItem._file_extent_item[0].unpack_from(data)
        if self.type != FILE_EXTENT_INLINE:
            # These are confusing, so they deserve a comment in the code:
            # (disk_bytenr EXTENT_ITEM disk_num_bytes) is the tree key of
            # the extent item storing the actual data.
            #
            # The third one, offset is the offset inside that extent where the
            # data we need starts. num_bytes is the amount of bytes to be used
            # from that offset onwards.
            #
            # Remember that these numbers always be multiples of disk block
            # sizes, because that's how it gets cowed. We don't just use 1 or 2
            # bytes from another extent.
            pos = FileExtentItem._file_extent_item[0].size
            self.disk_bytenr, self.disk_num_bytes, self.offset, self.num_bytes = \
                FileExtentItem._file_extent_item[1].unpack_from(data, pos)
        else:
            self._inline_encoded_nbytes = header.len - FileExtentItem._file_extent_item[0].size

    @property
    def compress_str(self):
        return _compress_type_str_map.get(self.compression, 'unknown')

    @property
    def type_str(self):
        return _file_extent_type_str_map.get(self.type, 'unknown')

    def __str__(self):
        ret = ["extent data at {self.logical_offset} generation {self.generation} "
               "ram_bytes {self.ram_bytes} "
               "compression {self.compress_str} type {self.type_str}".format(self=self)]
        if self.type != 0:
            ret.append("disk_bytenr {self.disk_bytenr} disk_num_bytes {self.disk_num_bytes} "
                       "offset {self.offset} num_bytes {self.num_bytes}".format(self=self))
        else:
            ret.append("inline_encoded_nbytes {self._inline_encoded_nbytes}".format(self=self))
        return ' '.join(ret)
