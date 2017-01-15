# Copyright (C) 2016-2017 Hans van Kranenburg <hans.van.kranenburg@mendix.com>
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

from __future__ import division, print_function, absolute_import, unicode_literals
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

SPACE_INFO_GLOBAL_RSV = 1 << 49

QGROUP_LEVEL_SHIFT = 48

EXTENT_FLAG_DATA = 1 << 0
EXTENT_FLAG_TREE_BLOCK = 1 << 1
BLOCK_FLAG_FULL_BACKREF = 1 << 8

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
        return "{0}/{1}".format(qgroup_level(objectid), qgroup_subvid(objectid))
    if _type == UUID_KEY_SUBVOL or _type == UUID_KEY_RECEIVED_SUBVOL:
        return "0x{0:0>16x}".format(objectid)

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
        return "{0}/{1}".format(qgroup_level(offset), qgroup_subvid(offset))
    if _type == UUID_KEY_SUBVOL or _type == UUID_KEY_RECEIVED_SUBVOL:
        return "0x{0:0>16x}".format(offset)
    if offset == ULLONG_MAX:
        return '-1'

    return str(offset)


import btrfs.ioctl


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
        return "({0} {1} {2})".format(
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
    disk_key = struct.Struct("<QBQ")

    def __init__(self, buf, pos=0):
        super(DiskKey, self).__init__(*DiskKey.disk_key.unpack_from(buf, pos))


class FileSystem(object):
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY)
        self.fsid = self.fs_info().fsid

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
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
            yield DevItem(header, data)

    def chunks(self, min_vaddr=0, max_vaddr=ULLONG_MAX, nr_items=ULONG_MAX):
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, min_vaddr)
        max_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, max_vaddr)
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key,
                                               nr_items=nr_items):
            yield Chunk(header, data)

    def dev_extents(self, min_devid=1, max_devid=ULLONG_MAX):
        tree = DEV_TREE_OBJECTID
        min_key = btrfs.ctree.Key(min_devid, 0, 0)
        max_key = btrfs.ctree.Key(max_devid, 255, ULLONG_MAX)
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
            yield DevExtent(header, data)

    def block_group(self, vaddr, length=None):
        tree = EXTENT_TREE_OBJECTID
        min_offset = length if length is not None else 0
        max_offset = length if length is not None else ULLONG_MAX
        min_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, min_offset)
        max_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, max_offset)
        block_groups = [BlockGroupItem(header, data)
                        for header, data in
                        btrfs.ioctl.search(self.fd, tree, min_key, max_key, nr_items=1)]
        return block_groups[0]

    def extents(self, min_vaddr=0, max_vaddr=ULLONG_MAX,
                load_data_refs=False, load_metadata_refs=False):
        tree = EXTENT_TREE_OBJECTID
        min_key = Key(min_vaddr, 0, 0)
        max_key = Key(max_vaddr, 255, ULLONG_MAX)
        extent = None
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
            if header.type == EXTENT_ITEM_KEY:
                if extent is not None:
                    yield extent
                extent = ExtentItem(header, data, load_data_refs=load_data_refs,
                                    load_metadata_refs=load_metadata_refs)
            elif header.type == METADATA_ITEM_KEY:
                if extent is not None:
                    yield extent
                extent = MetaDataItem(header, data, load_refs=load_metadata_refs)
            elif header.type == EXTENT_DATA_REF_KEY and load_data_refs is True:
                extent.append_extent_data_ref(ExtentDataRef(header, data))
            elif header.type == SHARED_DATA_REF_KEY and load_data_refs is True:
                extent.append_shared_data_ref(SharedDataRef(header, data))
            elif header.type == TREE_BLOCK_REF_KEY and load_metadata_refs is True:
                extent.append_tree_block_ref(TreeBlockRef(header))
            elif header.type == SHARED_BLOCK_REF_KEY and load_metadata_refs is True:
                extent.append_shared_block_ref(SharedBlockRef(header))
            elif header.type != BLOCK_GROUP_ITEM_KEY:
                raise Exception("BUG: unexpected object {0}".format(
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
        for next_header, next_data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
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
                      for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key)]
        return subvol_ids


class DevItem(object):
    dev_item = struct.Struct("<3Q3L3QL2B16s16s")

    def __init__(self, header, buf, pos=0):
        self.key = Key(header.objectid, header.type, header.offset)
        self.devid, self.total_bytes, self.bytes_used, self.io_align, self.io_width, \
            self.sector_size, self.type, self.generation, self.start_offset, self.dev_group, \
            self.seek_speed, self.bandwidth, uuid_bytes, fsid_bytes = \
            DevItem.dev_item.unpack_from(buf, pos)
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.fsid = uuid.UUID(bytes=fsid_bytes)

    def __str__(self):
        return "dev item devid {0} total bytes {1} bytes used {2}".format(
            self.devid, self.total_bytes, self.bytes_used)


class Chunk(object):
    chunk = struct.Struct("<4Q3L2H")

    def __init__(self, header, buf, pos=0):
        self.key = Key(header.objectid, header.type, header.offset)
        self.vaddr = header.offset
        self.length, self.owner, self.stripe_len, self.type, self.io_align, \
            self.io_width, self.sector_size, self.num_stripes, self.sub_stripes = \
            Chunk.chunk.unpack_from(buf, pos)
        pos += Chunk.chunk.size
        self.stripes = [Stripe(self, buf, stripe_pos)
                        for stripe_pos in range(pos,
                                                pos + Stripe.stripe.size * self.num_stripes,
                                                Stripe.stripe.size)]

    def __str__(self):
        return "chunk vaddr {0} type {1} length {2} num_stripes {3}".format(
            self.vaddr, btrfs.utils.block_group_flags_str(self.type),
            self.length, self.num_stripes)


class Stripe(object):
    stripe = struct.Struct("<2Q16s")

    def __init__(self, chunk, buf, pos=0):
        self.chunk = chunk
        self.devid, self.offset, uuid_bytes = Stripe.stripe.unpack_from(buf, pos)
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "stripe devid {0} offset {1}".format(self.devid, self.offset)


class DevExtent(object):
    dev_extent = struct.Struct("<4Q16s")

    def __init__(self, header, buf, pos=0):
        self.key = Key(header.objectid, header.type, header.offset)
        self.devid = header.objectid
        self.paddr = header.offset
        self.chunk_tree, self.chunk_objectid, self.chunk_offset, self.length, uuid_bytes = \
            DevExtent.dev_extent.unpack_from(buf, pos)
        self.vaddr = self.chunk_offset
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "dev extent devid {0} paddr {1} length {2} chunk {3}".format(
            self.devid, self.paddr, self.length, self.chunk_offset)


class BlockGroupItem(object):
    block_group_item = struct.Struct("<3Q")

    def __init__(self, header, buf, pos=0):
        self.key = Key(header.objectid, header.type, header.offset)
        self.transid = header.transid
        self.vaddr = header.objectid
        self.length = header.offset
        self.used, self.chunk_objectid, self.flags = \
            BlockGroupItem.block_group_item.unpack_from(buf, pos)

    def __str__(self):
        return "block group vaddr {0} transid {1} length {2} flags {3} used {4} " \
            "used_pct {5}".format(self.vaddr, self.transid, self.length,
                                  btrfs.utils.block_group_flags_str(self.flags),
                                  self.used, int(round((self.used * 100) / self.length)))


class ExtentItem(object):
    extent_item = struct.Struct("<3Q")
    extent_inline_ref = struct.Struct("<BQ")

    def __init__(self, header, buf, pos=0, load_data_refs=False, load_metadata_refs=False):
        self.key = Key(header.objectid, header.type, header.offset)
        self.vaddr = header.objectid
        self.length = header.offset
        self.refs, self.generation, self.flags = ExtentItem.extent_item.unpack_from(buf, pos)
        pos += ExtentItem.extent_item.size
        if self.flags == EXTENT_FLAG_DATA and load_data_refs is True:
            self.extent_data_refs = []
            self.shared_data_refs = []
            while pos < len(buf):
                inline_ref_type, inline_ref_offset = \
                    ExtentItem.extent_inline_ref.unpack_from(buf, pos)
                if inline_ref_type == EXTENT_DATA_REF_KEY:
                    pos += 1
                    self.extent_data_refs.append(InlineExtentDataRef(buf, pos))
                    pos += InlineExtentDataRef.inline_extent_data_ref.size
                elif inline_ref_type == SHARED_DATA_REF_KEY:
                    pos += 1
                    self.shared_data_refs.append(InlineSharedDataRef(buf, pos))
                    pos += InlineSharedDataRef.inline_shared_data_ref.size
        elif self.flags & EXTENT_FLAG_TREE_BLOCK and load_metadata_refs is True:
            self.tree_block_info = TreeBlockInfo(buf, pos)
            pos += TreeBlockInfo.tree_block_info.size
            self.tree_block_refs = []
            self.shared_block_refs = []
            while pos < len(buf):
                inline_ref_type, inline_ref_offset = \
                    ExtentItem.extent_inline_ref.unpack_from(buf, pos)
                if inline_ref_type == TREE_BLOCK_REF_KEY:
                    self.tree_block_refs.append(InlineTreeBlockRef(inline_ref_offset))
                elif inline_ref_type == SHARED_BLOCK_REF_KEY:
                    self.shared_block_refs.append(InlineSharedBlockRef(inline_ref_offset))
                else:
                    raise Exception("BUG: expected inline TREE_BLOCK_REF or SHARED_BLOCK_REF_KEY "
                                    "but got {0}".format(str(buf[pos:])))
                pos += ExtentItem.extent_inline_ref.size

    def append_extent_data_ref(self, ref):
        self.extent_data_refs.append(ref)

    def append_shared_data_ref(self, ref):
        self.shared_data_refs.append(ref)

    def append_tree_block_ref(self, ref):
        self.tree_block_refs.append(ref)

    def append_shared_block_ref(self, ref):
        self.shared_block_refs.append(ref)

    def __str__(self):
        return "extent vaddr {0} length {1} refs {2} gen {3} flags {4}".format(
            self.vaddr, self.length, self.refs, self.generation,
            btrfs.utils.extent_flags_str(self.flags))


class ExtentDataRef(object):
    extent_data_ref = struct.Struct("<3QL")

    def __init__(self, header, buf, pos=0):
        self.root, self.objectid, self.offset, self.count = \
            ExtentDataRef.extent_data_ref.unpack_from(buf, pos)

    def __str__(self):
        return "extent data backref root {0} objectid {1} offset {2} count {3}".format(
            self.root, self.objectid, self.offset, self.count)


class InlineExtentDataRef(ExtentDataRef):
    inline_extent_data_ref = ExtentDataRef.extent_data_ref

    def __init__(self, buf, pos=0):
        self.root, self.objectid, self.offset, self.count = \
            InlineExtentDataRef.inline_extent_data_ref.unpack_from(buf, pos)

    def __str__(self):
        return "inline extent data backref root {0} objectid {1} offset {2} count {3}".format(
            self.root, self.objectid, self.offset, self.count)


class SharedDataRef(object):
    shared_data_ref = struct.Struct("<L")

    def __init__(self, header, buf, pos=0):
        self.parent = header.offset
        self.count, = SharedDataRef.shared_data_ref.unpack_from(buf, pos)

    def __str__(self):
        return "shared data backref parent {0} count {1}".format(self.parent, self.count)


class InlineSharedDataRef(SharedDataRef):
    inline_shared_data_ref = struct.Struct("<QL")

    def __init__(self, buf, pos=0):
        self.parent, self.count = InlineSharedDataRef.inline_shared_data_ref.unpack_from(buf, pos)

    def __str__(self):
        return "inline shared data backref parent {0} count {1}".format(self.parent, self.count)


class TreeBlockInfo(object):
    tree_block_info = struct.Struct("<QBQB")

    def __init__(self, buf, pos=0):
        tb_objectid, tb_type, tb_offset, self.level = \
            TreeBlockInfo.tree_block_info.unpack_from(buf, pos)
        self.key = Key(tb_objectid, tb_type, tb_offset)

    def __str__(self):
        return "tree block key {0} level {1}".format(self.key, self.level)


class MetaDataItem(object):
    def __init__(self, header, buf, pos=0, load_refs=False):
        self.key = Key(header.objectid, header.type, header.offset)
        self.vaddr = header.objectid
        self.skinny_level = header.offset
        self.refs, self.generation, self.flags = ExtentItem.extent_item.unpack_from(buf, pos)
        if load_refs is True:
            self._load_refs(buf, pos)

    def _load_refs(self, buf, pos):
        pos += ExtentItem.extent_item.size
        self.tree_block_refs = []
        self.shared_block_refs = []
        while pos < len(buf):
            inline_ref_type, inline_ref_offset = \
                ExtentItem.extent_inline_ref.unpack_from(buf, pos)
            if inline_ref_type == TREE_BLOCK_REF_KEY:
                self.tree_block_refs.append(InlineTreeBlockRef(inline_ref_offset))
            elif inline_ref_type == SHARED_BLOCK_REF_KEY:
                self.shared_block_refs.append(InlineSharedBlockRef(inline_ref_offset))
            else:
                raise Exception("BUG: expected inline TREE_BLOCK_REF or SHARED_BLOCK_REF_KEY "
                                "in METADATA_ITEM {0}, but got: {1}"
                                "".format(self.key, str(buf[pos:])))
            pos += ExtentItem.extent_inline_ref.size

    def append_tree_block_ref(self, ref):
        self.tree_block_refs.append(ref)

    def append_shared_block_ref(self, ref):
        self.shared_block_refs.append(ref)

    def __str__(self):
        return "metadata vaddr {0} refs {1} gen {2} flags {3} skinny level {4}".format(
            self.vaddr, self.refs, self.generation,
            btrfs.utils.extent_flags_str(self.flags), self.skinny_level)


class TreeBlockRef(object):
    def __init__(self, header):
        self.root = header.offset

    def __str__(self):
        return "tree block backref root {0}".format(key_objectid_str(self.root, None))


class InlineTreeBlockRef(TreeBlockRef):
    def __init__(self, root):
        self.root = root

    def __str__(self):
        return "inline tree block backref root {0}".format(key_objectid_str(self.root, None))


class SharedBlockRef(object):
    def __init__(self, header):
        self.parent = header.offset

    def __str__(self):
        return "shared block backref parent {0}".format(self.parent)


class InlineSharedBlockRef(SharedBlockRef):
    def __init__(self, parent):
        self.parent = parent

    def __str__(self):
        return "inline shared block backref parent {0}".format(self.parent)


class TimeSpec(object):
    timespec = struct.Struct("<QL")

    def __init__(self, buf, pos=0):
        self.sec, self.nsec = TimeSpec.timespec.unpack_from(buf, pos)


class InodeItem(object):
    _inode_item = [
        struct.Struct("<5Q4L3Q32x"),
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
    ]
    inode_item = struct.Struct("<" + ''.join([s.format[1:].decode() for s in _inode_item]))

    def __init__(self, header, buf, pos=0):
        if header is not None:
            self.key = Key(header.objectid, header.type, header.offset)
        else:
            self.key = None
        self.generation, self.transid, self.size, self.nbytes, self.block_group, \
            self.nlink, self.uid, self.gid, self.mode, self.rdev, self.flags, self.sequence = \
            InodeItem._inode_item[0].unpack_from(buf, pos)
        pos += InodeItem._inode_item[0].size
        self.atime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size
        self.ctime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size
        self.mtime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size
        self.otime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size

    def __str__(self):
        return "inode generation {0} transid {1} size {2} nbytes {3} block_group {4} mode {5} " \
            "links {6} uid {7} gid {8} rdev {9} flags {10}({11})".format(
                self.generation, self.transid, self.size, self.nbytes, self.block_group,
                oct(self.mode), self.nlink, self.uid, self.gid, self.rdev, hex(self.flags),
                btrfs.utils.flags_str(self.flags, _inode_flags_str_map))


class RootItem(object):
    _root_item = [
        InodeItem.inode_item,
        struct.Struct("<7QL"),
        DiskKey.disk_key,
        struct.Struct("<BBQ16s16s16s4Q"),
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
        TimeSpec.timespec,
    ]
    root_item = struct.Struct("<" + ''.join([s.format[1:].decode() for s in _root_item]))

    def __init__(self, header, buf, pos=0):
        self.key = Key(header.objectid, header.type, header.offset)
        self.inode = InodeItem(None, buf, pos)
        pos += InodeItem.inode_item.size
        self.generation, self.dirid, self.bytenr, self.byte_limit, self.bytes_used, \
            self.last_snapshot, self.flags, self.refs = \
            RootItem._root_item[1].unpack_from(buf, pos)
        pos += RootItem._root_item[1].size
        self.drop_progress = DiskKey(buf, pos)
        pos += DiskKey.disk_key.size
        self.drop_level, self.level, self.generation_v2, uuid_bytes, parent_uuid_bytes, \
            received_uuid_bytes, self.ctransid, self.otransid, self.stransid, self.rtransid = \
            RootItem._root_item[3].unpack_from(buf, pos)
        pos += RootItem._root_item[3].size
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.parent_uuid = uuid.UUID(bytes=parent_uuid_bytes)
        self.received_uuid = uuid.UUID(bytes=received_uuid_bytes)
        self.ctime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size
        self.otime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size
        self.stime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size
        self.rtime = TimeSpec(buf, pos)
        pos += TimeSpec.timespec.size

    def __str__(self):
        return "root uuid {0} dirid {1} gen {2} last_snapshot {3} flags {4}({5})".format(
            self.uuid, self.dirid, self.generation, self.last_snapshot,
            hex(self.flags), btrfs.utils.flags_str(self.flags, _root_flags_str_map))
