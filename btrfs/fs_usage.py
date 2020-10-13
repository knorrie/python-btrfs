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

"""
This module provides advanced usage reporting for a btrfs filesystem.

By calling the :func:`~btrfs.ctree.FileSystem.usage` function on a
:class:`btrfs.ctree.FileSystem` object, an :class:`FsUsage` object is returned
that can be inspected.

Example::

    >>> import btrfs
    >>> with btrfs.FileSystem('/') as fs:
    ...     usage = fs.usage()
    ...     btrfs.utils.pretty_print(usage)

.. note::

    If you're not yet familiar with it, btrfs terminology can be quite
    confusing.

    Here's just an example: In btrfs terminology, a ‘space’ is the collection
    of all block groups that have identical type and profile flags. For
    example, Metadata, DUP is a ‘space’. The word ‘space’ is also used for the
    distinction between ‘physical address space’ and ‘virtual address space’.

"""

import btrfs
import copy
from btrfs.ctree import (  # noqa
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    BLOCK_GROUP_TYPE_MASK, BLOCK_GROUP_PROFILE_MASK,
)


class DevSpaceUsage(object):
    """Physical usage details for a single space per device.

    For example, a `Data, DUP` chunk of 1GiB results in a 2GiB allocation of
    physical bytes on the device. A `Data, RAID5` chunk of 3GiB, allocated over
    4 devices results in a 1GiB allocation on each device, with 256MiB reserved
    for parity.

    :ivar int flags: Block group type and profile, e.g. `Data, RAID1`.
    :ivar int devid: Device ID
    :ivar int allocated: Total amount of allocated physical bytes.
    :ivar int parity: Amount of allocated physical bytes reserved for parity.

    .. note::
        Objects of this type are provided as part of an :class:`FsUsage` object.

    """
    def __init__(self, devid, flags):
        self.flags = flags
        self.devid = devid
        self.allocated = 0
        self.parity = 0

    def _add_usage(self, allocated, parity):
        self.allocated += allocated
        self.parity += parity

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.block_group_flags_str, 'flags'),
            (btrfs.utils.pretty_size, 'allocated'),
            (btrfs.utils.pretty_size, 'parity'),
        ]


class DevUsage(object):
    """Physical usage details for a device.

    :ivar int devid: Device ID
    :ivar int total: Total amount of bytes.
    :ivar int allocated: Total amount of allocated bytes.
    :ivar dev_space_usage: Allocated and parity bytes per space for this
        device, indexed by space flags.
    :vartype dev_space_usage: dict of DevSpaceUsage
    :ivar int unallocatable: Physical bytes that are not allocatable because of
        unbalanced device sizes.
    :ivar int unallocatable_reclaimable: Physical bytes that are not
        allocatable because of unbalanced allocations.

    .. note::
        Objects of this type are provided as part of an :class:`FsUsage` object.

    """
    def __init__(self, device):
        self.devid = device.devid
        self.total = device.total_bytes
        self.allocated = device.bytes_used
        self.unallocated = self.total - self.allocated
        self.dev_space_usage = {}
        self.unallocatable_soft = None  # set during FsUsage init
        self.unallocatable_hard = None  # set during FsUsage init
        self.unallocatable_reclaimable = None  # set during FsUsage init

    def _dev_space_usage_key_str(flags):
        return btrfs.utils.block_group_flags_str(flags)

    def _add_usage(self, flags, allocated, parity):
        if flags not in self.dev_space_usage:
            self.dev_space_usage[flags] = DevSpaceUsage(self.devid, flags)
        self.dev_space_usage[flags]._add_usage(allocated, parity)

    def _init_unallocatable_reclaimable(self):
        self.unallocatable_reclaimable = \
            max(self.unallocatable_soft - self.unallocatable_hard, 0)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'total'),
            (btrfs.utils.pretty_size, 'allocated'),
            (btrfs.utils.pretty_size, 'unallocated'),
            (btrfs.utils.pretty_size, 'unallocatable_soft'),
            (btrfs.utils.pretty_size, 'unallocatable_hard'),
            (btrfs.utils.pretty_size, 'unallocatable_reclaimable'),
        ]


class RawSpaceUsage(object):
    """Physical usage details per space.

    For example, if the `Metadata, RAID1` space has a 2GiB size in terms of
    virtual addressing, in which 768MiB is used, then the allocated physical
    size is 4GiB and amount of physical bytes used is 1.5GiB. A `Data, RAID6`
    space of 8GiB, consisting of two 4GiB block groups (virtual address space),
    each distributed over 6 devices, will occupy 2*(4+2) = 12 GiB physical
    allocated bytes and have 4GiB of allocated bytes reserved for parity
    blocks.

    :ivar int flags: Block group type and profile, e.g. `Data, RAID1`.
    :ivar int allocated: Total amount of allocated bytes.
    :ivar int parity: Total amount of allocated bytes reserved for parity
        blocks.
    :ivar int used: Total amount of physical bytes used.

    .. note::
        Objects of this type are provided as part of an :class:`FsUsage` object.

    """
    def __init__(self, space):
        self.flags = space.flags
        ratio = btrfs.volumes.block_group_profile_ncopies(space.flags)
        self.allocated = space.total_bytes * ratio  # initially missing parity blocks
        self.used = space.used_bytes * ratio
        self.parity = 0

    def _add_usage(self, parity):
        self.allocated += parity
        self.parity += parity

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.block_group_flags_str, 'flags'),
            (btrfs.utils.pretty_size, 'allocated'),
            (btrfs.utils.pretty_size, 'parity'),
            (btrfs.utils.pretty_size, 'used'),
        ]


class BlockGroupTypeUsage(object):
    """Physical usage details per block group type.

    Totals per block group type (`System`, `Data`, `Metadata`, or,
    `Data+Metadata` for mixed mode), disregarding the block group profile
    (`Single`, `RAID1`, etc).

    :ivar int type: Block group type, e.g. `Metadata`.
    :ivar int allocated: Total amount of allocated bytes.
    :ivar int parity: Total amount of allocated bytes reserved for parity
        blocks.
    :ivar int used: Total amount of physical bytes used.

    .. note::
        Objects of this type are provided as part of an :class:`FsUsage` object.

    """
    def __init__(self, block_group_type):
        self.type = block_group_type
        self.allocated = 0
        self.used = 0
        self.parity = 0

    def _add_usage(self, allocated, parity, used):
        self.allocated += allocated
        self.parity += parity
        self.used += used

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.block_group_flags_str, 'type'),
            (btrfs.utils.pretty_size, 'allocated'),
            (btrfs.utils.pretty_size, 'parity'),
            (btrfs.utils.pretty_size, 'used'),
        ]


class VirtualSpaceUsage(object):
    """Virtual usage per space.

    :ivar int flags: Block group type and profile, e.g. `Data, RAID1`.
    :ivar int total: Total amount of allocated bytes for this space.
    :ivar int used: Total amount of virtual bytes used.

    .. note::
        Objects of this type are provided as part of an :class:`FsUsage` object.

    """
    def __init__(self, space):
        self.flags = space.flags
        self.total = space.total_bytes
        self.used = space.used_bytes

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.block_group_flags_str, 'flags'),
            (btrfs.utils.pretty_size, 'total'),
            (btrfs.utils.pretty_size, 'used'),
        ]


class VirtualBlockGroupTypeUsage(object):
    """Virtual address space usage per block group type.

    Totals for the virtual address space per block group type (`System`,
    `Data`, `Metadata`, or, `Data+Metadata` for mixed mode), disregarding the
    block group profile (`Single`, `RAID1`, etc).

    :ivar int flags: Block group type, e.g. `Metadata`.
    :ivar int total: Total amount of allocated bytes.
    :ivar int used: Total amount of virtual bytes used.
    :ivar int unused: Amount of allocated but unused virtual bytes.

    .. note::
        Objects of this type are provided as part of an :class:`FsUsage` object.

    """
    def __init__(self, block_group_type):
        self.type = block_group_type
        self.total = 0
        self.used = 0
        self.unused = None

    def _add_usage(self, total, used):
        self.total += total
        self.used += used
        self.unused = self.total - self.used

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.block_group_flags_str, 'type'),
            (btrfs.utils.pretty_size, 'total'),
            (btrfs.utils.pretty_size, 'used'),
            (btrfs.utils.pretty_size, 'unused'),
        ]


class FsUsage(object):
    """Detailed usage information for a file system.

    When creating an object of this type, the first argument, fs, is mandatory.
    The other arguments can be used to influence the simulation to predict free
    space and unallocatable space with explicit hints instead of using
    information from the current filesystem, This is used by the
    space-calculator program to run the simulation starting with a completely
    empty filesystem.

    :param btrfs.ctree.FileSystem fs: Filesystem to examine.
    :param int data_metadata_ratio: Data to metadata ratio to use when running
        the simulation to predict free space and unallocatable space.
    :param int target_profile_metadata: Explicitly set metadata profile to use
        for new allocations when running the simulation to predict free
        and unallocatable space (not for a mixed filesystem).
    :param int target_profile_data: Explicitly set data profile to use for new
        allocations when running the simulation to predict free and
        unallocatable space (not for a mixed filesystem).
    :param int target_profile_mixed: Explicitly set metadata and data profile
        to use for new allocations when running the simulation to predict free
        and unallocatable space (only for a mixed filesystem).

    Target block group profiles (used for new chunk allocations):

    :ivar int target_profile_system: Profile for new System chunk allocations.
    :ivar int target_profile_metadata: Profile for new Metadata chunk
        allocations (not for a mixed filesystem).
    :ivar int target_profile_data: Profile for new Data chunk allocations (not
        for a mixed filesystem).
    :ivar int target_profile_mixed: Profile for new Data+Metadata chunk
        allocations (only for a mixed filesystem).

    Usage details for the physical address space:

    :ivar int total: Total amount of physical bytes in the filesystem.
    :ivar int allocated: Total amount of allocated physical bytes.
    :ivar int parity: Total amount of allocated bytes reserved for parity
        blocks.
    :ivar dev_usage: Physical usage details per device, indexed by Device ID.
    :vartype dev_usage: dict of DevUsage
    :ivar block_group_type_usage: Physical usage details per block group type,
        indexed by block group type.
    :vartype block_group_type_usage: dict of BlockGroupTypeUsage
    :ivar raw_space_usage: Physical usage details per space, indexed by space
        flags.
    :vartype raw_space_usage: dict of RawSpaceUsage

    Usage details for the virtual address space:

    :ivar int virtual_total: Total amount of virtual address space.
    :ivar int virtual_used: Total amount of bytes used inside the virtual
        address space.
    :ivar virtual_block_group_type_usage: Virtual address space usage per block
        group type, indexed by block group type.
    :vartype virtual_block_group_type_usage: dict of VirtualBlockGroupTypeUsage
    :ivar VirtualSpaceUsage virtual_space_usage: Virtual usage per space,
        indexed by space flags.
    :vartype virtual_space_usage: dict of VirtualSpaceUsage

    Allocatable space information:

    The *soft* unallocatable amount of bytes is the currently unallocatable
    part of the physical bytes on attached devices because the allocations in
    the filesystem are unbalanced. This value is estimated by extrapolating the
    current usage pattern and simulating new chunk allocations using the
    current target allocation profiles. By doing so, we also discover how much
    extra *virtual* address space these allocations would result in.

    :ivar int unallocatable_soft: Unallocatable physical disk space because of
        unbalanced allocations.
    :ivar int estimated_allocatable_virtual_metadata: Estimated amount of
        virtual address space bytes that can be added by allocating physical
        bytes for metadata, based on the current usage pattern (not for a mixed
        filesystem).
    :ivar int estimated_allocatable_virtual_data: Estimated amount of virtual
        address space bytes that can be added by allocating physical bytes for
        data, based on the current usage pattern (not for a mixed filesystem).
    :ivar int estimated_allocatable_virtual_mixed: Estimated amount of virtual
        address space bytes that can be added by allocating physical bytes for
        metadata and data,, based on the current usage pattern (only for a
        mixed filesystem).

    The *hard* unallocatable amount of bytes is the amount of physical bytes
    that cannot be used for allocations, because of having different sizes of
    devices attached. These values are unallocatable disk space that remains
    after trying to simulate data and metadata allocations in a ratio similar
    to current usage, starting with all disks being empty.

    :ivar int unallocatable_hard: Unallocatable physical disk space because of
        unbalanced device sizes.
    :ivar int estimated_full_allocatable_virtual_metadata: Estimated amount of
        virtual address space bytes for metadata, in case of optimally balanced
        allocations. (not for a mixed filesystem).
    :ivar int estimated_full_allocatable_virtual_data: Estimated amount of
        virtual address space bytes for data, in case of optimally balanced
        allocations. (not for a mixed filesystem).
    :ivar int estimated_full_allocatable_virtual_mixed: Estimated amount of
        virtual address space bytes for metadata and data, in case of optimally
        balanced allocations. (only for a mixed filesystem).

    The difference between *soft* and *hard* unallocatable bytes is the amount
    of physical disk space that can be reclaimed for allocations when
    rebalancing the filesystem.

    :ivar int unallocatable_reclaimable: Unallocatable physical bytes that can
        be reclaimed when balancing the filesystem.

    Some other totals for convenience:

    :ivar int allocatable: The total amount of physical bytes that are
        allocatable in this filesystem. I.e. total size minus
        unallocatable_soft.
    :ivar int allocatable_left: The amount of allocatable physical bytes
        remaining, until the filesystem will report being out of space, given
        current usage pattern and target profiles.

    By combining the unused virtual space in already allocated chunks and
    estimated allocatable virtual bytes, we get actual numbers of estimated
    free space. I.e., what we would like df to show us.

    :ivar int free_metadata: Estimated virtual space left to use for metadata
        (not for a mixed filesystem).
    :ivar int free_data: Estimated virtual space left to use for data (not for
        a mixed filesystem).
    :ivar int free_mixed: Estimated virtual space left to use for metadata and
        data (only for a mixed filesystem).

    """
    def __init__(self, fs, data_metadata_ratio=None,
                 target_profile_metadata=None,
                 target_profile_data=None,
                 target_profile_mixed=None):
        self._mixed_groups = fs.mixed_groups()

        # Spaces and devices are a source of information
        spaces = [
            space
            for space in fs.space_info()
            if space.flags != btrfs.ctree.SPACE_INFO_GLOBAL_RSV
        ]
        devices = list(fs.devices())

        self.raw_space_usage = {
            space.flags: RawSpaceUsage(space)
            for space in spaces
        }
        self.dev_usage = {
            device.devid: DevUsage(device)
            for device in devices
        }
        self.total = sum(
            device.total_bytes
            for device in devices
        )
        self.allocated = sum(
            device.bytes_used
            for device in devices
        )
        self.parity = 0

        BLOCK_GROUP_MIXED = btrfs.BLOCK_GROUP_METADATA | btrfs.BLOCK_GROUP_DATA
        if not self._mixed_groups:
            if target_profile_metadata is not None:
                self.target_profile_system = target_profile_metadata | btrfs.BLOCK_GROUP_SYSTEM
                self.target_profile_metadata = target_profile_metadata | btrfs.BLOCK_GROUP_METADATA
            if target_profile_data is not None:
                self.target_profile_data = target_profile_data | btrfs.BLOCK_GROUP_DATA
        else:
            if target_profile_mixed is not None:
                self.target_profile_system = target_profile_mixed | btrfs.BLOCK_GROUP_SYSTEM
                self.target_profile_mixed = target_profile_mixed | BLOCK_GROUP_MIXED

        # We walk the chunk list because every block group / chunk can be laid
        # out over any amount of disks. To collect e.g. the amount of parity
        # bytes, we need to look at all of them.
        #
        # Confusing: chunk.type is actually all the flags, so type and profile
        # combined.
        for chunk in fs.chunks():
            flags = chunk.type
            if flags not in self.raw_space_usage:
                continue  # A conversion to this profile just started right now?
            # Remember last seen chunk types as target profiles
            block_group_type = flags & BLOCK_GROUP_TYPE_MASK
            if block_group_type == BLOCK_GROUP_SYSTEM:
                self.target_profile_system = flags
            elif not self._mixed_groups:
                if block_group_type == BLOCK_GROUP_DATA:
                    self.target_profile_data = flags
                elif block_group_type == BLOCK_GROUP_METADATA:
                    self.target_profile_metadata = flags
            else:
                self.target_profile_mixed = flags

            dev_extent_length = btrfs.volumes.chunk_to_dev_extent_length(chunk)
            chunk_raw_parity_bytes = btrfs.volumes.chunk_to_raw_parity_bytes(chunk)
            self.parity += chunk_raw_parity_bytes
            self.raw_space_usage[flags]._add_usage(chunk_raw_parity_bytes)
            dev_extent_parity_bytes = chunk_raw_parity_bytes // len(chunk.stripes)
            for stripe in chunk.stripes:
                if stripe.devid not in self.dev_usage:
                    continue  # A device just got added?
                self.dev_usage[stripe.devid]._add_usage(flags,
                                                        dev_extent_length,
                                                        dev_extent_parity_bytes)

        # Combine information from different spaces with same chunk type into
        # totals per block group type. So, e.g. all DATA space, regardless of
        # being single, RAID1, etc...
        self.block_group_type_usage = {}
        for raw_space in self.raw_space_usage.values():
            space_type = raw_space.flags & BLOCK_GROUP_TYPE_MASK
            if space_type not in self.block_group_type_usage:
                self.block_group_type_usage[space_type] = BlockGroupTypeUsage(space_type)
            self.block_group_type_usage[space_type]._add_usage(
                    raw_space.allocated, raw_space.parity, raw_space.used)

        self.virtual_space_usage = {
            space.flags: VirtualSpaceUsage(space)
            for space in spaces
        }

        # Combine information from different spaces with same chunk type into
        # totals per block group type. So, e.g. all DATA space, regardless of
        # being single, RAID1, etc...
        self.virtual_block_group_type_usage = {}

        for virtual_space in self.virtual_space_usage.values():
            space_type = virtual_space.flags & BLOCK_GROUP_TYPE_MASK
            if space_type not in self.virtual_block_group_type_usage:
                self.virtual_block_group_type_usage[space_type] = \
                        VirtualBlockGroupTypeUsage(space_type)
            self.virtual_block_group_type_usage[space_type]._add_usage(
                    virtual_space.total, virtual_space.used)

        # The total size of the block groups in the virtual address space
        self.virtual_total = sum(
            virtual_space.total
            for virtual_space in self.virtual_space_usage.values()
        )

        self.virtual_used = sum(
            virtual_space.used
            for virtual_space in self.virtual_space_usage.values()
        )

        if data_metadata_ratio is not None:
            self.default_data_metadata_ratio = data_metadata_ratio
        else:
            self.default_data_metadata_ratio = 200

        # Estimate the amount of unallocatable raw disk space if the sizes of
        # attached block devices are unbalanced. We start the simulation with
        # the entire sizes of the attached devices and keep allocating chunks
        # until not possible any more.
        #
        device_sizes = {
            devid: dev_usage.total
            for devid, dev_usage in self.dev_usage.items()
        }
        if not self._mixed_groups:
            # The estimated "full" allocatable numbers are the estimation of
            # virtual space to be used for data and metadata when the
            # filesystem would be totally empty to begin with.
            #
            # This is e.g. used by the space calculator example.
            dev_unallocatable_hard, \
                self.estimated_full_allocatable_virtual_metadata, \
                self.estimated_full_allocatable_virtual_data = \
                self._simulate_chunk_allocations(device_sizes)
        else:
            dev_unallocatable_hard, \
                self.estimated_full_allocatable_virtual_mixed = \
                self._simulate_chunk_allocations(device_sizes)
        for devid, unallocatable_hard in dev_unallocatable_hard.items():
            self.dev_usage[devid].unallocatable_hard = unallocatable_hard
        self.unallocatable_hard = sum(dev_unallocatable_hard.values())

        # Next, we estimate the amount of unallocatable raw disk space when
        # starting out with the current state of the filesystem.
        unallocated_sizes = {
            devid: dev_usage.unallocated
            for devid, dev_usage in self.dev_usage.items()
        }
        if not self._mixed_groups:
            dev_unallocatable_soft, \
                self.estimated_allocatable_virtual_metadata, \
                self.estimated_allocatable_virtual_data = \
                self._simulate_chunk_allocations(unallocated_sizes)
        else:
            dev_unallocatable_soft, \
                self.estimated_allocatable_virtual_mixed = \
                self._simulate_chunk_allocations(unallocated_sizes)
        for devid, unallocatable_soft in dev_unallocatable_soft.items():
            self.dev_usage[devid].unallocatable_soft = unallocatable_soft
        self.unallocatable_soft = sum(dev_unallocatable_soft.values())

        # At this point, it is possible that the unallocatable_hard amounts are
        # higher than the unallocatable_soft amounts. E.g. if we just switched
        # to another target profile. In that case, this means we can not fully
        # rewrite all data to the target profile!

        # For convenience reasons, we provide a few more derived numbers...
        #
        # If the soft unallocatable amount of bytes is higher than the hard
        # amount, we can reclaim space by balancing the filesytsem.
        self.unallocatable_reclaimable = \
            max(self.unallocatable_soft - self.unallocatable_hard, 0)
        for dev_usage in self.dev_usage.values():
            dev_usage._init_unallocatable_reclaimable()

        self.allocatable = self.total - self.unallocatable_soft
        self.allocatable_left = self.allocatable - self.allocated

        if not self._mixed_groups:
            self.free_metadata = self.estimated_allocatable_virtual_metadata
            if btrfs.BLOCK_GROUP_METADATA in self.virtual_block_group_type_usage:
                self.free_metadata += \
                    self.virtual_block_group_type_usage[btrfs.BLOCK_GROUP_METADATA].unused
            self.free_data = self.estimated_allocatable_virtual_data
            if btrfs.BLOCK_GROUP_DATA in self.virtual_block_group_type_usage:
                self.free_data += \
                    self.virtual_block_group_type_usage[btrfs.BLOCK_GROUP_DATA].unused
        else:
            self.free_mixed = self.estimated_allocatable_virtual_mixed
            if BLOCK_GROUP_MIXED in self.virtual_block_group_type_usage:
                self.free_mixed += \
                    self.virtual_block_group_type_usage[BLOCK_GROUP_MIXED].unused

    def _raw_space_usage_key_str(flags):
        return btrfs.utils.block_group_flags_str(flags)

    def _block_group_type_usage_key_str(block_group_type):
        return btrfs.utils.block_group_flags_str(block_group_type)

    def _virtual_space_usage_key_str(flags):
        return btrfs.utils.block_group_flags_str(flags)

    def _virtual_block_group_type_usage_key_str(block_group_type):
        return btrfs.utils.block_group_flags_str(block_group_type)

    def _data_metadata_ratio(self):
        """
        Determine data to metadata ratio for allocation simulation for wasted space.

        E.g. a ratio of 200 means that for every X bytes of metadata, we can
        allocate 200*X bytes for data.

        Actual simulation ratio is a weighted combination of the current data to
        metadata ratio and the default of 200, where the weight of the current
        ratio increases if the filesystem is filled up more.

        If an empty filesystem is presented (this is used for the space
        calculator), then just use the default that was set earlier.
        """
        if self._mixed_groups:
            raise ValueError("Data to metadata ratio is irrelevant for mixed groups.")
        if BLOCK_GROUP_METADATA not in self.virtual_block_group_type_usage:
            return self.default_data_metadata_ratio
        used_fraction = self.virtual_used / self.total
        used_metadata = self.virtual_block_group_type_usage[BLOCK_GROUP_METADATA].used
        used_data = self.virtual_block_group_type_usage[BLOCK_GROUP_DATA].used
        used_ratio = used_data / used_metadata
        return used_fraction * used_ratio + (1 - used_fraction) * self.default_data_metadata_ratio

    def _alloc_chunk(self, sizes, flags):
        """
        This is used by the wasted space calculator.

        sizes is a dictionary {devid: allocatable_bytes, ...}
              which will be modified in place as side effect
        flags contains allocation type, which is DATA (also for mixed) or METADATA

        This function tries to reduce unallocated raw bytes on each disk in a way
        similar to the workings of the btrfs chunk allocator. The sizes dictionary
        will be modified in place while doing so. When returning False, no chunk
        allocation is possible any more, and sizes will show the amount of
        unallocatable bytes per device.
        """
        attrs = btrfs.volumes._raid_attrs(flags & BLOCK_GROUP_PROFILE_MASK)
        if flags & BLOCK_GROUP_DATA:
            max_stripe_size = btrfs.utils.SZ_1G
            max_chunk_size = btrfs.volumes.BTRFS_MAX_DATA_CHUNK_SIZE
        elif flags & BLOCK_GROUP_METADATA:
            if self.total > 50 * btrfs.utils.SZ_1G:
                max_stripe_size = btrfs.utils.SZ_1G
            else:
                max_stripe_size = btrfs.utils.SZ_256M
            max_chunk_size = max_stripe_size
        else:
            raise ValueError("Only DATA and METADATA supported here")
        # we don't want a chunk larger than 10% of writeable space
        max_chunk_size = min(self.total // 10, max_chunk_size)
        # [(devid, unallocated), ...], most unallocated space per device first
        non_zero_sizes = {
            devid: unallocated
            for devid, unallocated in sizes.items()
            if unallocated > 0
        }
        sorted_sizes = sorted(list(non_zero_sizes.items()), key=lambda x: -x[1])
        # Keep a multiple of devs_increment, chop off the rest
        sorted_sizes = sorted_sizes[:len(sorted_sizes) -
                                    (len(sorted_sizes) % attrs.devs_increment)]
        if len(sorted_sizes) < attrs.devs_min:
            return 0
        # Keep only the amount we need for a single chunk allocation
        if attrs.devs_max != 0:
            sorted_sizes = sorted_sizes[:min(len(sorted_sizes), attrs.devs_max)]
        # Actual device extent size is limited by the device with least amount of
        # available space and by max_stripe_size.
        stripe_size = min(max_stripe_size, sorted_sizes[-1][1] // attrs.dev_stripes)
        # But, there's another limit, the max_chunk_size...
        num_stripes = len(sorted_sizes) * attrs.dev_stripes
        chunk_size = btrfs.volumes.dev_extent_length_to_chunk_length(
                flags, num_stripes, stripe_size)
        if chunk_size > max_chunk_size:
            stripe_size = btrfs.volumes.chunk_length_to_dev_extent_length(
                    flags, num_stripes, max_chunk_size)
            chunk_size = max_chunk_size
        # Finally, decrease unallocated space
        for devid, _ in sorted_sizes:
            sizes[devid] -= stripe_size * attrs.dev_stripes
        return chunk_size

    def _simulate_chunk_allocations(self, sizes):
        """
        Try to do metadata and data allocations until no longer possible. The sizes
        dictionary is modified in place and lists the amount of unallocatable space
        per disk when the function returns.
        """
        _sizes = copy.deepcopy(sizes)  # copy will be modified in place
        if not self._mixed_groups:
            ratio = self._data_metadata_ratio()
            metadata_flags = self.target_profile_metadata
            data_flags = self.target_profile_data
            virtual_data = 0
            virtual_metadata = 0
            while True:
                chunk_size = self._alloc_chunk(_sizes, metadata_flags)
                if chunk_size == 0:
                    return _sizes, virtual_metadata, virtual_data
                virtual_metadata += chunk_size
                while virtual_data / virtual_metadata < ratio:
                    chunk_size = self._alloc_chunk(_sizes, data_flags)
                    if chunk_size == 0:
                        return _sizes, virtual_metadata, virtual_data
                    virtual_data += chunk_size
        else:
            flags = self.target_profile_mixed
            virtual_mixed = 0
            while True:
                chunk_size = self._alloc_chunk(_sizes, flags)
                if chunk_size == 0:
                    return _sizes, virtual_mixed
                virtual_mixed += chunk_size

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.space_profile_description, 'target_profile_system'),
            (btrfs.utils.space_profile_description, 'target_profile_metadata'),
            (btrfs.utils.space_profile_description, 'target_profile_data'),
            (btrfs.utils.space_profile_description, 'target_profile_mixed'),
            (btrfs.utils.btrfs.utils.pretty_size, 'total'),
            (btrfs.utils.btrfs.utils.pretty_size, 'allocated'),
            (btrfs.utils.btrfs.utils.pretty_size, 'parity'),
            (btrfs.utils.btrfs.utils.pretty_size, 'virtual_total'),
            (btrfs.utils.btrfs.utils.pretty_size, 'virtual_used'),
            (btrfs.utils.btrfs.utils.pretty_size, 'unalloctable_soft'),
            (btrfs.utils.btrfs.utils.pretty_size, 'estimated_allocatable_virtual_metadata'),
            (btrfs.utils.btrfs.utils.pretty_size, 'estimated_allocatable_virtual_data'),
            (btrfs.utils.btrfs.utils.pretty_size, 'estimated_allocatable_virtual_mixed'),
            (btrfs.utils.btrfs.utils.pretty_size, 'unallocatable_hard'),
            (btrfs.utils.btrfs.utils.pretty_size, 'estimated_full_allocatable_virtual_metadata'),
            (btrfs.utils.btrfs.utils.pretty_size, 'estimated_full_allocatable_virtual_data'),
            (btrfs.utils.btrfs.utils.pretty_size, 'estimated_full_allocatable_virtual_mixed'),
            (btrfs.utils.btrfs.utils.pretty_size, 'unallocatable_reclaimable'),
            (btrfs.utils.btrfs.utils.pretty_size, 'allocatable'),
            (btrfs.utils.btrfs.utils.pretty_size, 'allocatable_left'),
            (btrfs.utils.btrfs.utils.pretty_size, 'free_metadata'),
            (btrfs.utils.btrfs.utils.pretty_size, 'free_data'),
            (btrfs.utils.btrfs.utils.pretty_size, 'free_mixed'),
        ]
