# Copyright (C) 2018 Hans van Kranenburg <hans@knorrie.org>
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


from btrfs.ctree import (  # noqa
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_TYPE_MASK,
    BLOCK_GROUP_RAID0, BLOCK_GROUP_RAID1, BLOCK_GROUP_RAID5,
    BLOCK_GROUP_RAID6, BLOCK_GROUP_DUP, BLOCK_GROUP_RAID10,
    BLOCK_GROUP_SINGLE,
    BLOCK_GROUP_PROFILE_MASK,
)
from collections import namedtuple

_RaidAttr = namedtuple('RaidAttr', [
    'sub_stripes', 'dev_stripes', 'devs_max', 'devs_min', 'tolerated_failures',
    'devs_increment', 'ncopies', 'nparity', 'raid_name', 'bg_flag',
])

RAID_RAID10 = 0
RAID_RAID1 = 1
RAID_DUP = 2
RAID_RAID0 = 3
RAID_SINGLE = 4
RAID_RAID5 = 5
RAID_RAID6 = 6


def _bg_flags_to_raid_index(flags):
    """Convert block group flags to an index to access _raid_array"""
    if flags & BLOCK_GROUP_RAID10:
        return RAID_RAID10
    if flags & BLOCK_GROUP_RAID1:
        return RAID_RAID1
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
    return chunk_length_to_dev_extent_length(chunk.type, chunk.num_stripes, chunk.length)


def dev_extent_length_to_chunk_length(flags, num_stripes, stripe_size):
    # In here, we simply reverse the calculation of chunk length to dev extent
    # length.
    attrs = _raid_attrs(flags & BLOCK_GROUP_PROFILE_MASK)
    num_data_stripes = num_stripes - attrs.nparity
    # stripe_size is a synonym for device extent length.
    raw_data_bytes = stripe_size * num_data_stripes
    chunk_length = raw_data_bytes // attrs.ncopies
    return chunk_length


def chunk_to_raw_parity_bytes(chunk):
    dev_extent_length = chunk_to_dev_extent_length(chunk)
    attrs = _raid_attrs(chunk.type & BLOCK_GROUP_PROFILE_MASK)
    return dev_extent_length * attrs.nparity


def block_group_profile_ncopies(flags):
    attrs = _raid_attrs(flags & BLOCK_GROUP_PROFILE_MASK)
    return attrs.ncopies
