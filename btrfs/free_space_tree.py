# Copyright (C) 2017 Hans van Kranenburg <hans@knorrie.org>
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
This module contains a small helper, which is used by the
:func:`~btrfs.ctree.FreeSpaceBitmap.unpack` function of a
:class:`btrfs.ctree.FreeSpaceBitmap`. It's also used by the
:func:`~btrfs.ctree.FileSystem.free_space_extents` convenience method of a
:class:`btrfs.ctree.FileSystem` object for generating a simple stream of free
space extent info transparently unpacking bitmaps.
"""


from collections import namedtuple


FreeSpaceExtent = namedtuple('FreeSpaceExtent', ['vaddr', 'length'])
