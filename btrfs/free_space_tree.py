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

"""
This module contains a small helper, which is used by the
:func:`~btrfs.ctree.FreeSpaceBitmap.unpack` function of a
:class:`btrfs.ctree.FreeSpaceBitmap`. It's also used by the
:func:`~btrfs.ctree.FileSystem.free_space_extents` convenience method of a
:class:`btrfs.ctree.FileSystem` object for generating a simple stream of free
space extent info transparently unpacking bitmaps.
"""


from collections import namedtuple


FreeSpaceExtent = namedtuple('FreeSpaceExtent', ['vaddr', 'length'])
