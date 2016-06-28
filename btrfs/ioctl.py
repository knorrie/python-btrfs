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

from __future__ import division, print_function, absolute_import, unicode_literals
from collections import namedtuple
import array
import fcntl
import itertools
import struct
import uuid

ULLONG_MAX = (1 << 64) - 1
ULONG_MAX = (1 << 32) - 1

BTRFS_IOCTL_MAGIC = 0x94

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


def _IOC(_dir, _type, nr, size):
    return (_dir << _IOC_DIRSHIFT) | (_type << _IOC_TYPESHIFT) | \
        (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


def _IO(_type, nr):
    return _IOC(_IOC_NONE, _type, nr, 0)


def _IOR(_type, nr, _struct):
    return _IOC(_IOC_READ, _type, nr, _struct.size)


def _IOW(_type, nr, _struct):
    return _IOC(_IOC_WRITE, _type, nr, _struct.size)


def _IOWR(_type, nr, _struct):
    return _IOC(_IOC_READ | _IOC_WRITE, _type, nr, _struct.size)


DEVICE_PATH_NAME_MAX = 1024

from btrfs.ctree import BLOCK_GROUP_TYPE_MASK, SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_PROFILE_MASK
import btrfs.ctree


def create_buf(size=4096):
    return array.array(b'B', itertools.repeat(0, size))


ioctl_fs_info_args = struct.Struct("=QQ16sLLL980x")
IOC_FS_INFO = _IOR(BTRFS_IOCTL_MAGIC, 31, ioctl_fs_info_args)


class FsInfo(object):
    def __init__(self, fd):
        buf = create_buf(ioctl_fs_info_args.size)
        fcntl.ioctl(fd, IOC_FS_INFO, buf)
        self.max_id, self.num_devices, fsid_bytes, self.nodesize, self.sectorsize, \
            self.clone_alignment = ioctl_fs_info_args.unpack(buf)
        self.fsid = uuid.UUID(bytes=fsid_bytes)

    def __str__(self):
        return "max_id {0} num_devices {1} fsid {2} nodesize {3} sectorsize {4} " \
            "clone_alignment {5}".format(self.max_id, self.num_devices, self.fsid, self.nodesize,
                                         self.sectorsize, self.clone_alignment)


ioctl_dev_info_args = struct.Struct("=Q16sQQ3032x{0}s".format(DEVICE_PATH_NAME_MAX))
IOC_DEV_INFO = _IOWR(BTRFS_IOCTL_MAGIC, 30, ioctl_dev_info_args)


class DevInfo(object):
    def __init__(self, fd, devid):
        buf = create_buf(ioctl_dev_info_args.size)
        ioctl_dev_info_args.pack_into(buf, 0, devid, b'', 0, 0, b'')
        fcntl.ioctl(fd, IOC_DEV_INFO, buf)
        self.devid, uuid_bytes, self.bytes_used, self.total_bytes, path_bytes = \
            ioctl_dev_info_args.unpack(buf)
        self.path = path_bytes.decode()
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "devid {0} uuid {1} bytes_used {2} total_bytes {3} path {4}".format(
            self.devid, self.uuid, self.bytes_used, self.total_bytes, self.path)


ioctl_space_args = struct.Struct("=2Q")
ioctl_space_info = struct.Struct("=3Q")
IOC_SPACE_INFO = _IOWR(BTRFS_IOCTL_MAGIC, 20, ioctl_space_args)
SpaceArgs = namedtuple('SpaceArgs', ['space_slots', 'total_spaces'])


class SpaceInfo(object):
    def __init__(self, buf, pos):
        self.flags, self.total_bytes, self.used_bytes = ioctl_space_info.unpack_from(buf, pos)
        self.type = self.flags & (BLOCK_GROUP_TYPE_MASK | SPACE_INFO_GLOBAL_RSV)
        self.profile = self.flags & BLOCK_GROUP_PROFILE_MASK
        self.ratio = btrfs.utils.block_group_profile_ratio(self.profile)
        self.raw_total_bytes = self.total_bytes * self.ratio
        self.raw_used_bytes = self.used_bytes * self.ratio

    def __str__(self):
        return "{0}, {1}: total={2}, used={3}".format(
            btrfs.utils.block_group_type_str(self.flags),
            btrfs.utils.block_group_profile_str(self.flags),
            btrfs.utils.pretty_size(self.total_bytes),
            btrfs.utils.pretty_size(self.used_bytes))


def space_args(fd):
    buf = create_buf(ioctl_space_args.size)
    fcntl.ioctl(fd, IOC_SPACE_INFO, buf)
    return SpaceArgs(*ioctl_space_args.unpack(buf))


def space_info(fd):
    args = space_args(fd)
    buf_size = ioctl_space_args.size + ioctl_space_info.size * args.total_spaces
    buf = create_buf(buf_size)
    ioctl_space_args.pack_into(buf, 0, args.total_spaces, 0)
    fcntl.ioctl(fd, IOC_SPACE_INFO, buf)
    return [SpaceInfo(buf, pos)
            for pos in range(ioctl_space_args.size, buf_size, ioctl_space_info.size)]


ioctl_search_key = struct.Struct("=Q6QLLL4x32x")
ioctl_search_args = struct.Struct("{0}{1}x".format(
    ioctl_search_key.format.decode(), 4096 - ioctl_search_key.size))
ioctl_search_header = struct.Struct("=3Q2L")
IOC_TREE_SEARCH = _IOWR(BTRFS_IOCTL_MAGIC, 17, ioctl_search_args)
SearchHeader = namedtuple('SearchHeader', ['transid', 'objectid', 'offset', 'type', 'len'])


def search(fd, tree, min_key=None, max_key=None,
           transid_min=0, transid_max=ULLONG_MAX,
           nr_items=ULONG_MAX):
    if min_key is None:
        min_key = btrfs.ctree.Key(0, 0, 0)
    if max_key is None:
        max_key = btrfs.ctree.Key(ULLONG_MAX, 255, ULLONG_MAX)
    wanted_nr_items = nr_items
    result_nr_items = -1
    buf = create_buf(4096)
    while min_key <= max_key and result_nr_items != 0 and wanted_nr_items > 0:
        ioctl_search_key.pack_into(buf, 0, tree,
                                   min_key.objectid, max_key.objectid,
                                   min_key.offset, max_key.offset,
                                   transid_min, transid_max,
                                   min_key.type, max_key.type,
                                   wanted_nr_items)
        fcntl.ioctl(fd, IOC_TREE_SEARCH, buf)
        result_nr_items = ioctl_search_key.unpack_from(buf, 0)[9]
        if result_nr_items > 0:
            pos = ioctl_search_key.size
            for i in range(result_nr_items):
                header = SearchHeader(*ioctl_search_header.unpack_from(buf, pos))
                pos += ioctl_search_header.size
                data = buf[pos:pos+header.len]
                yield((header, data))
                pos += header.len
                wanted_nr_items -= 1
                if wanted_nr_items == 0:
                    break
            min_key = btrfs.ctree.Key(header.objectid, header.type, header.offset)
            min_key += 1
