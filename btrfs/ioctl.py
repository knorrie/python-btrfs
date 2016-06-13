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

from collections import namedtuple
import array
import btrfs.ctree
import fcntl
import itertools
import struct

ULLONG_MAX = (1 << 64) - 1
ULONG_MAX = (1 << 32) - 1


def create_buf(size=4096):
    return array.array("B", itertools.repeat(0, size))


IOC_SPACE_INFO = 0xc0109414

ioctl_space_args = struct.Struct("=2Q")
ioctl_space_info = struct.Struct("=3Q")

SpaceArgs = namedtuple('SpaceArgs', ['space_slots', 'total_spaces'])
SpaceInfo = namedtuple('SpaceInfo', ['flags', 'total_bytes', 'used_bytes'])


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
    return [SpaceInfo(*ioctl_space_info.unpack_from(buf, pos))
            for pos in xrange(ioctl_space_args.size, buf_size, ioctl_space_info.size)]


IOC_TREE_SEARCH = 0xd0009411

ioctl_search_key = struct.Struct("=Q6QLLL4x32x")
ioctl_search_header = struct.Struct("=3Q2L")

SearchHeader = namedtuple('SearchHeader', ['transid', 'objectid', 'offset', 'type', 'len'])


def search(fd, tree, min_key, max_key=None,
           transid_min=0, transid_max=ULLONG_MAX,
           nr_items=ULONG_MAX):
    if max_key is None:
        max_key = btrfs.ctree.Key(ULLONG_MAX, 255, ULLONG_MAX)
    result_nr_items = -1
    buf = create_buf(4096)
    while min_key <= max_key and result_nr_items != 0:
        ioctl_search_key.pack_into(buf, 0, tree,
                                   min_key.objectid, max_key.objectid,
                                   min_key.offset, max_key.offset,
                                   transid_min, transid_max,
                                   min_key.type, max_key.type,
                                   nr_items)
        fcntl.ioctl(fd, IOC_TREE_SEARCH, buf)
        result_nr_items = ioctl_search_key.unpack_from(buf, 0)[9]
        if result_nr_items > 0:
            pos = ioctl_search_key.size
            for i in xrange(result_nr_items):
                header = SearchHeader(*ioctl_search_header.unpack_from(buf, pos))
                pos += ioctl_search_header.size
                data = buf[pos:pos+header.len]
                yield((header, data))
                pos += header.len
            min_key = btrfs.ctree.Key(header.objectid, header.type, header.offset)
            min_key += 1
