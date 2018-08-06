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
from btrfs.utils import SZ_1G
from collections import namedtuple

BTRFS_MAX_DATA_CHUNK_SIZE = 10 * SZ_1G

RaidAttr = namedtuple('RaidAttr', [
    'sub_stripes', 'dev_stripes', 'devs_max', 'devs_min', 'tolerated_failures',
    'devs_increment', 'ncopies', 'nparity',
])

_raid_attrs = {
    BLOCK_GROUP_RAID10: RaidAttr(
        sub_stripes=2,
        dev_stripes=1,
        devs_max=0,
        devs_min=4,
        tolerated_failures=1,
        devs_increment=2,
        ncopies=2,
        nparity=0,
    ),
    BLOCK_GROUP_RAID1: RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=2,
        devs_min=2,
        tolerated_failures=1,
        devs_increment=2,
        ncopies=2,
        nparity=0,
    ),
    BLOCK_GROUP_DUP: RaidAttr(
        sub_stripes=1,
        dev_stripes=2,
        devs_max=1,
        devs_min=1,
        tolerated_failures=0,
        devs_increment=1,
        ncopies=2,
        nparity=0,
    ),
    BLOCK_GROUP_RAID0: RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=0,
        devs_min=2,
        tolerated_failures=0,
        devs_increment=1,
        ncopies=1,
        nparity=0,
    ),
    BLOCK_GROUP_SINGLE: RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=1,
        devs_min=1,
        tolerated_failures=0,
        devs_increment=1,
        ncopies=1,
        nparity=0,
    ),
    BLOCK_GROUP_RAID5: RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=0,
        devs_min=2,
        tolerated_failures=1,
        devs_increment=1,
        ncopies=1,
        nparity=1,
    ),
    BLOCK_GROUP_RAID6: RaidAttr(
        sub_stripes=1,
        dev_stripes=1,
        devs_max=0,
        devs_min=3,
        tolerated_failures=2,
        devs_increment=1,
        ncopies=1,
        nparity=2,
    ),
}


def chunk_length_to_dev_extent_length(flags, num_stripes, chunk_length):
    # So, we start with a chunk length, which is the amount of usable virtual
    # space.
    attrs = _raid_attrs[flags & BLOCK_GROUP_PROFILE_MASK]
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
    return chunk_length_to_dev_extent_length(chunk.type, len(chunk.stripes), chunk.length)


def dev_extent_length_to_chunk_length(flags, num_stripes, stripe_size):
    # In here, we simply reverse the calculation of chunk length to dev extent
    # length.
    attrs = _raid_attrs[flags & BLOCK_GROUP_PROFILE_MASK]
    num_data_stripes = num_stripes - attrs.nparity
    # stripe_size is a synonym for device extent length.
    raw_data_bytes = stripe_size * num_data_stripes
    chunk_length = raw_data_bytes // attrs.ncopies
    return chunk_length


def chunk_to_raw_parity_bytes(chunk):
    dev_extent_length = chunk_to_dev_extent_length(chunk)
    attrs = _raid_attrs[chunk.type & BLOCK_GROUP_PROFILE_MASK]
    return dev_extent_length * attrs.nparity


def block_group_profile_ncopies(flags):
    attrs = _raid_attrs[flags & BLOCK_GROUP_PROFILE_MASK]
    return attrs.ncopies
