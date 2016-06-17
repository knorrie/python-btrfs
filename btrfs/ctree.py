# Copyright (C) 2016 Hans van Kranenburg <hans.van.kranenburg@mendix.com>
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
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 021110-1307, USA.

from btrfs.ioctl import ULLONG_MAX
import btrfs.ioctl
import copy
import os
import struct
import uuid


def ULL(n):
    if n < 0:
        return n + (1 << 64)
    return n


DEV_ITEMS_OBJECTID = 1
ROOT_TREE_OBJECTID = 1
EXTENT_TREE_OBJECTID = 2
CHUNK_TREE_OBJECTID = 3
FIRST_CHUNK_TREE_OBJECTID = 256
ORPHAN_OBJECTID = ULL(-5)

ORPHAN_ITEM_KEY = 48
EXTENT_ITEM_KEY = 168
EXTENT_DATA_REF_KEY = 178
SHARED_DATA_REF_KEY = 184
BLOCK_GROUP_ITEM_KEY = 192
DEV_ITEM_KEY = 216
CHUNK_ITEM_KEY = 228

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
    BLOCK_GROUP_RAID1 |
    BLOCK_GROUP_RAID5 |
    BLOCK_GROUP_RAID6 |
    BLOCK_GROUP_DUP |
    BLOCK_GROUP_RAID10
)

SPACE_INFO_GLOBAL_RSV = 1 << 49

EXTENT_FLAG_DATA = 1 << 0
EXTENT_FLAG_TREE_BLOCK = 1 << 1
BLOCK_FLAG_FULL_BACKREF = 1 << 1


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
        return "({0} {1} {2})".format(self._objectid, self._type, self._offset)

    def __add__(self, amount):
        new_key = copy.copy(self)
        new_key.key += amount
        return new_key


class FileSystem(object):
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY)

    def space_info(self):
        return btrfs.ioctl.space_info(self.fd)

    def devices(self):
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(DEV_ITEMS_OBJECTID, DEV_ITEM_KEY, 0)
        max_key = Key(DEV_ITEMS_OBJECTID, DEV_ITEM_KEY, ULLONG_MAX)
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
            yield Device(header, data)

    def chunks(self):
        tree = CHUNK_TREE_OBJECTID
        min_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, 0)
        max_key = Key(FIRST_CHUNK_TREE_OBJECTID, CHUNK_ITEM_KEY, ULLONG_MAX)
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
            yield Chunk(header, data)

    def block_group(self, vaddr):
        tree = EXTENT_TREE_OBJECTID
        min_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, 0)
        max_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, ULLONG_MAX)
        block_groups = [BlockGroup(header, data)
                        for header, data in
                        btrfs.ioctl.search(self.fd, tree, min_key, max_key, nr_items=1)]
        return block_groups[0]

    def extents(self, min_vaddr=0, max_vaddr=ULLONG_MAX):
        tree = EXTENT_TREE_OBJECTID
        min_key = Key(min_vaddr, 0, 0)
        max_key = Key(max_vaddr, 255, ULLONG_MAX)
        extent = None
        for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key):
            if header.type == BLOCK_GROUP_ITEM_KEY:
                continue
            elif header.type == EXTENT_ITEM_KEY:
                if extent is not None:
                    yield extent
                extent = Extent(header, data)
            elif header.type == EXTENT_DATA_REF_KEY:
                extent.append_extent_data_ref(header, data)
            elif header.type == SHARED_DATA_REF_KEY:
                extent.append_shared_data_ref(header, data)

        if extent is not None:
            yield extent

    def orphan_subvol_ids(self):
        tree = ROOT_TREE_OBJECTID
        min_key = Key(ORPHAN_OBJECTID, ORPHAN_ITEM_KEY, 0)
        max_key = Key(ORPHAN_OBJECTID, ORPHAN_ITEM_KEY, ULLONG_MAX)
        subvol_ids = [header.offset
                      for header, data in btrfs.ioctl.search(self.fd, tree, min_key, max_key)]
        return subvol_ids


class Device(object):
    dev_item = struct.Struct("<3Q3L3QL2B16s16s")

    def __init__(self, header, data):
        self.devid, self.total_bytes, self.bytes_used, self.io_align, self.io_width, \
            self.sector_size, self.type, self.generation, self.start_offset, self.dev_group, \
            self.seek_speed, self.bandwidth, uuid_bytes, fsid_bytes = \
            Device.dev_item.unpack_from(data, 0)
        self.uuid = uuid.UUID(bytes=uuid_bytes)
        self.fsid = uuid.UUID(bytes=fsid_bytes)


class Chunk(object):
    chunk = struct.Struct("<4Q3L2H")

    def __init__(self, header, data):
        self.vaddr = header.offset
        self.length, self.owner, self.stripe_len, self.type, self.io_align, \
            self.io_width, self.sector_size, self.num_stripes, self.sub_stripes = \
            Chunk.chunk.unpack_from(data, 0)
        pos = Chunk.chunk.size
        self.stripes = [Stripe(data, stripe_pos)
                        for stripe_pos in xrange(pos,
                                                 pos + Stripe.stripe.size * self.num_stripes,
                                                 Stripe.stripe.size)]


class Stripe(object):
    stripe = struct.Struct("<2Q16s")

    def __init__(self, data, pos=0):
        self.devid, self.offset, uuid_bytes = Stripe.stripe.unpack_from(data, pos)
        self.uuid = uuid.UUID(bytes=uuid_bytes)


class BlockGroup(object):
    block_group_item = struct.Struct("<3Q")

    def __init__(self, header, data):
        self.vaddr = header.objectid
        self.length = header.offset
        self.used, self.chunk_objectid, self.flags = \
            BlockGroup.block_group_item.unpack_from(data, 0)


class Extent(object):
    extent_item = struct.Struct("<3Q")
    extent_inline_ref = struct.Struct("<BQ")

    def __init__(self, header, data):
        self.vaddr = header.objectid
        self.length = header.offset
        self.refs, self.generation, self.flags = Extent.extent_item.unpack_from(data, 0)
        self.extent_data_refs = []
        self.shared_data_refs = []
        pos = Extent.extent_item.size
        while pos < len(data):
            inline_ref_type, inline_ref_offset = Extent.extent_inline_ref.unpack_from(data, pos)
            if self.flags == EXTENT_FLAG_DATA:
                if inline_ref_type == EXTENT_DATA_REF_KEY:
                    pos += 1
                    self.extent_data_refs.append(ExtentDataRef(data, pos))
                    pos += ExtentDataRef.extent_data_ref.size
                elif inline_ref_type == SHARED_DATA_REF_KEY:
                    pos += 1
                    self.shared_data_refs.append(SharedDataRef(data, pos))
                    pos += SharedDataRef.shared_data_ref.size

    def append_extent_data_ref(self, header, data):
        self.extent_data_refs.append(ExtentDataRef(data, 0))

    def append_shared_data_ref(self, header, data):
        self.shared_data_refs.append(SharedDataRef(data, 0))


class ExtentDataRef(object):
    extent_data_ref = struct.Struct("<3QL")

    def __init__(self, data, pos=0):
        self.root, self.objectid, self.offset, self.count = \
            ExtentDataRef.extent_data_ref.unpack_from(data, pos)


class SharedDataRef(object):
    shared_data_ref = struct.Struct("<QL")

    def __init__(self, data, pos):
        self.parent, self.count = SharedDataRef.shared_data_ref.unpack_from(data, pos)