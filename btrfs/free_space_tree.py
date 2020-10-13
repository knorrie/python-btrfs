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


class FreeSpaceExtent():
    """Helper object for listing free space tree extents.

    In the free space tree, information about free space can be stored as free
    space extent item, in which case it has information about a single gap of
    free space. Alternatively, it can be stored in a compacted format, as free
    space bitmap. In that case, to find out where the tiny gaps of free space
    are located, the bitmap needs to be unpacked.

    This object serves as a helper when doing so. It is used by the
    :func:`~btrfs.ctree.FreeSpaceBitmap.unpack` function of a
    :class:`btrfs.ctree.FreeSpaceBitmap`. It's also used by the
    :func:`~btrfs.ctree.FileSystem.free_space_extents` convenience method of a
    :class:`btrfs.ctree.FileSystem` object for generating a simple stream of free
    space extent info transparently unpacking bitmaps.

    :ivar int vaddr: Logical address of the start of the free space extent.
    :ivar int length: Length of the free space extent.
    """
    def __init__(self, vaddr, length):
        self.vaddr = vaddr
        self.length = length

    def __str__(self):
        return "free space extent vaddr {self.vaddr} length {self.length}".format(self=self)
