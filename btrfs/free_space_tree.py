# Copyright (C) 2017 Hans van Kranenburg <hans@knorrie.org>
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

from collections import namedtuple


FreeSpaceExtent = namedtuple('FreeSpaceExtent', ['vaddr', 'length'])


def unpack_bitmap(offset, sectorsize, bitmap):
    prev_bit = 0
    for cur_byte in bitmap:
        for bitnr in range(8):
            bit = 1 & (cur_byte >> bitnr)
            if prev_bit == 0 and bit == 1:
                extent_start = offset
            elif prev_bit == 1 and bit == 0:
                yield FreeSpaceExtent(extent_start, offset - extent_start)
            prev_bit = bit
            offset += sectorsize
    if prev_bit == 1:
        yield FreeSpaceExtent(extent_start, offset - extent_start)
