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

import btrfs.ioctl
import os


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


class FileSystem(object):
    def __init__(self, path):
        self.path = path
        self.fd = os.open(path, os.O_RDONLY)

    def space_info(self):
        return btrfs.ioctl.space_info(self.fd)
