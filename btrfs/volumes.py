# Copyright (C) 2018 Hans van Kranenburg <hans@knorrie.org>
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


from btrfs.ctree import (  # noqa
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_TYPE_MASK,
    BLOCK_GROUP_RAID0, BLOCK_GROUP_RAID1, BLOCK_GROUP_RAID5,
    BLOCK_GROUP_RAID1C3, BLOCK_GROUP_RAID1C4,
    BLOCK_GROUP_RAID6, BLOCK_GROUP_DUP, BLOCK_GROUP_RAID10,
    BLOCK_GROUP_SINGLE,
    BLOCK_GROUP_PROFILE_MASK,
)
from btrfs.utils import SZ_1G
from collections import namedtuple

BTRFS_MAX_DATA_CHUNK_SIZE = 10 * SZ_1G

_RaidAttr = namedtuple('RaidAttr', [
    'sub_stripes', 'dev_stripes', 'devs_max', 'devs_min', 'tolerated_failures',
    'devs_increment', 'ncopies', 'nparity', 'raid_name', 'bg_flag',
])

RAID_RAID10 = 0
RAID_RAID1 = 1
RAID_RAID1C3 = 2
RAID_RAID1C4 = 3
RAID_DUP = 4
RAID_RAID0 = 5
RAID_SINGLE = 6
RAID_RAID5 = 7
RAID_RAID6 = 8


def _bg_flags_to_raid_index(flags):
    """Convert block group flags to an index to access _raid_array"""
    if flags & BLOCK_GROUP_RAID10:
        return RAID_RAID10
    if flags & BLOCK_GROUP_RAID1:
        return RAID_RAID1
    if flags & BLOCK_GROUP_RAID1C3:
        return RAID_RAID1C3
    if flags & BLOCK_GROUP_RAID1C4:
        return RAID_RAID1C4
    if flags & BLOCK_GROUP_DUP:
        return RAID_DUP
    if flags & BLOCK_GROUP_RAID0:
        return RAID_RAID0
    if flags & BLOCK_GROUP_RAID5:
        return RAID_RAID5
    if flags & BLOCK_GROUP_RAID6:
        return RAID_RAID6
    return RAID_SINGLE


_raid_array = [
    _RaidAttr(
        sub_stripes=2,
        dev_stripes=1,
        devs_max=0,
        devs_min=4,
        tolerated_failures=1,
        devs_increment=2,
        ncopies=2,
        nparity=0,
        raid_name='raid10',
        bg_flag=BLOCK_GROUP_RAID10,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=2,
        devs_min=2,
        tolerated_failures=1,
        devs_increment=2,
        ncopies=2,
        nparity=0,
        raid_name='raid1',
        bg_flag=BLOCK_GROUP_RAID1,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=3,
        devs_min=3,
        tolerated_failures=2,
        devs_increment=3,
        ncopies=3,
        nparity=0,
        raid_name='raid1c3',
        bg_flag=BLOCK_GROUP_RAID1C3,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=4,
        devs_min=4,
        tolerated_failures=3,
        devs_increment=4,
        ncopies=4,
        nparity=0,
        raid_name='raid1c4',
        bg_flag=BLOCK_GROUP_RAID1C4,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=2,
        devs_max=1,
        devs_min=1,
        tolerated_failures=0,
        devs_increment=1,
        ncopies=2,
        nparity=0,
        raid_name='dup',
        bg_flag=BLOCK_GROUP_DUP,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=0,
        devs_min=2,
        tolerated_failures=0,
        devs_increment=1,
        ncopies=1,
        nparity=0,
        raid_name='raid0',
        bg_flag=BLOCK_GROUP_RAID0,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=1,
        devs_min=1,
        tolerated_failures=0,
        devs_increment=1,
        ncopies=1,
        nparity=0,
        raid_name='single',
        bg_flag=BLOCK_GROUP_SINGLE,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=0,
        devs_min=2,
        tolerated_failures=1,
        devs_increment=1,
        ncopies=1,
        nparity=1,
        raid_name='raid5',
        bg_flag=BLOCK_GROUP_RAID5,
    ),
    _RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=0,
        devs_min=3,
        tolerated_failures=2,
        devs_increment=1,
        ncopies=1,
        nparity=2,
        raid_name='raid6',
        bg_flag=BLOCK_GROUP_RAID6,
    ),
]


def _raid_attrs(flags):
    return _raid_array[_bg_flags_to_raid_index(flags)]


def chunk_length_to_dev_extent_length(flags, num_stripes, chunk_length):
    """Given information about a :class:`~btrfs.ctree.Chunk`, calculate the
    length of :class:`~btrfs.ctree.DevExtent` objects that store the Chunk
    data.

    For example, a Data, RAID6 block group of 8GiB, distributed over 6 devices,
    will occupy 2GiB * (4+2) = 12 GiB physical allocated bytes since it has
    4GiB of allocated bytes reserved for parity:

    Example::

        >>> btrfs.utils.pretty_size(
        ...     btrfs.volumes.chunk_length_to_dev_extent_length(
        ...         btrfs.ctree.BLOCK_GROUP_RAID6, 6, 8 * btrfs.utils.SZ_1G))
        '2.00GiB'
    """
    # So, we start with a chunk length, which is the amount of usable virtual
    # space.
    attrs = _raid_attrs(flags & BLOCK_GROUP_PROFILE_MASK)
    # The nparity attribute means that we have nparity * dev_extent_length of
    # raw space in total, dedicated for parity. These parity bytes can be
    # distributed over all of the num_stripes. If we subtract nparity from
    # num_stripes, we get the amount of dev_extent_lengths worth that contain
    # only data.
    #
    # For simplicity, let's assume all parity lives within dedicated device
    # extents. In reality it robins around, but that doesn't matter for our
    # calculations.
    #
    # RAID5: D | D | D | P
    # RAID6: D | D | D | P | P
    num_data_stripes = num_stripes - attrs.nparity
    # In case of profiles that duplicate data, we have to correct for that.
    # So, if we multiply the chunk_length (which is virtual space) by the
    # amount of copies of the data, we get the amount of raw bytes that we have
    # to fit in num_data_stripes amount of device extents.
    raw_data_bytes = chunk_length * attrs.ncopies
    dev_extent_length = raw_data_bytes // num_data_stripes
    return dev_extent_length


def chunk_to_dev_extent_length(chunk):
    """Given a :class:`~btrfs.ctree.Chunk` object, calculate the length of
    :class:`~btrfs.ctree.DevExtent` objects that store the chunk data.

    Example::

        >>> with btrfs.FileSystem('/') as fs:
        ...     chunk = list(fs.chunks(min_vaddr=3250585600, nr_items=1))[0]
        ...     print(chunk)
        ...     dev_extent_length = btrfs.volumes.chunk_to_dev_extent_length(chunk)
        ...     print("device extent length is {}".format(
        ...         btrfs.utils.pretty_size(dev_extent_length)))
        ...
        chunk vaddr 3250585600 type DATA|RAID5 length 2147483648 num_stripes 3
        device extent length is 1.00GiB
    """
    return chunk_length_to_dev_extent_length(chunk.type, chunk.num_stripes, chunk.length)


def dev_extent_length_to_chunk_length(flags, num_stripes, stripe_size):
    """This function simply reverses the calculation of
    :class:`~btrfs.ctree.Chunk` length to :class:`~btrfs.ctree.DevExtent`
    length.

    Example::

        >>> btrfs.utils.pretty_size(
        ...     btrfs.volumes.dev_extent_length_to_chunk_length(
        ...         btrfs.ctree.BLOCK_GROUP_RAID6, 6, 2 * btrfs.utils.SZ_1G))
        '8.00GiB'
    """
    attrs = _raid_attrs(flags & BLOCK_GROUP_PROFILE_MASK)
    num_data_stripes = num_stripes - attrs.nparity
    # stripe_size is a synonym for device extent length.
    raw_data_bytes = stripe_size * num_data_stripes
    chunk_length = raw_data_bytes // attrs.ncopies
    return chunk_length


def chunk_to_raw_parity_bytes(chunk):
    """Given a :class:`~btrfs.ctree.Chunk` object, calculate how many bytes are
    reserved for storing parity data for RAID56 profiles.

    This number is relevant to understand how much raw disk space that is
    allocated but not used is actually not usable for data, because it's
    reserved for parity.

    Example::

        >>> with btrfs.FileSystem('/mnt/tutorial') as fs:
        ...  chunk = list(fs.chunks(min_vaddr=3250585600, nr_items=1))[0]
        ...  print(chunk)
        ...  parity_bytes = btrfs.volumes.chunk_to_raw_parity_bytes(chunk)
        ...  print("amount of raw parity bytes: {}".format(
        ...      btrfs.utils.pretty_size(parity_bytes)))
        ...
        chunk vaddr 3250585600 type DATA|RAID5 length 2147483648 num_stripes 3
        amount of raw parity bytes: 1.00GiB
    """
    dev_extent_length = chunk_to_dev_extent_length(chunk)
    attrs = _raid_attrs(chunk.type & BLOCK_GROUP_PROFILE_MASK)
    return dev_extent_length * attrs.nparity


def block_group_profile_ncopies(flags):
    """This function returns how many times the actual data is replicated on
    disk given block group flags as input. E.g. for RAID1 this is 2, but for
    RAID5, this is just 1. The actual data is stored once in case of RAID5, and
    the redundancy is done using parity blocks, not data itself.

    Example::

        >>> btrfs.volumes.block_group_profile_ncopies(btrfs.ctree.BLOCK_GROUP_RAID10)
        2
    """
    attrs = _raid_attrs(flags & BLOCK_GROUP_PROFILE_MASK)
    return attrs.ncopies
