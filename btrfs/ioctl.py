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
import fcntl
import itertools
import struct


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
