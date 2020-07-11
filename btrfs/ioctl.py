# Copyright (C) 2016 Hans van Kranenburg <hans@knorrie.org>
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
This module contains the implementation of the calling side of several kernel
ioctl functions, as well as Python object representations of related C structs.

For convenience reasons, many of the functions can be called implicitly by
calling utility functions on a :class:`btrfs.ctree.FileSystem` object.
"""

from collections import namedtuple
import array
import btrfs
import errno
import fcntl
import os
import platform
import struct
import uuid

ULLONG_MAX = (1 << 64) - 1
ULONG_MAX = (1 << 32) - 1

BTRFS_IOCTL_MAGIC = 0x94

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8

# Here's an educated guess of what to do. A more fool-proof way of doing this would
# be to make a compiled extension instead, delivering the right values, but...
# that hasn't been done yet!
arch = platform.machine()
if arch in ('x86_64', 'i686', 'i386', 'i586', 'amd64', 'ia64', 'm68k', 'i486') \
        or arch.startswith(('aarch64', 'arm', 's390')):
    _IOC_SIZEBITS = 14
    _IOC_DIRBITS = 2
    _IOC_NONE = 0
    _IOC_WRITE = 1
    _IOC_READ = 2
elif arch in ('powerpc', 'alpha') or arch.startswith(('sparc', 'ppc', 'mips')):
    _IOC_SIZEBITS = 13
    _IOC_DIRBITS = 3
    _IOC_NONE = 1
    _IOC_READ = 2
    _IOC_WRITE = 4
elif arch == 'hppa' or arch.startswith('parisc'):
    _IOC_SIZEBITS = 14
    _IOC_DIRBITS = 2
    _IOC_NONE = 0
    _IOC_WRITE = 2
    _IOC_READ = 1
else:
    raise Exception("Unsupported machine type {}, please report as bug.".format(arch))

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS


def _IOC(_dir, _type, nr, size):
    return (_dir << _IOC_DIRSHIFT) | (_type << _IOC_TYPESHIFT) | \
        (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


def _IO(_type, nr):
    return _IOC(_IOC_NONE, _type, nr, 0)


def _IOR(_type, nr, _struct):
    return _IOC(_IOC_READ, _type, nr, _struct.size)


def _IOW(_type, nr, _struct):
    return _IOC(_IOC_WRITE, _type, nr, _struct.size)


def _IOWR(_type, nr, _struct):
    return _IOC(_IOC_READ | _IOC_WRITE, _type, nr, _struct.size)


DEVICE_PATH_NAME_MAX = 1024

ioctl_fs_info_args = struct.Struct('=QQ16sLLL980x')
IOC_FS_INFO = _IOR(BTRFS_IOCTL_MAGIC, 31, ioctl_fs_info_args)


class FsInfo(object):
    """Object representation of struct `btrfs_ioctl_fs_info_args`.

    :ivar int max_id: Highest device id of currently attached devices.
    :ivar int num_devices: Amount of devices attached to the filesystem.
    :ivar uuid.UUID fsid: Filesystem ID.
    :ivar int nodesize: B-tree node size (same as leaf size).
    :ivar int sectorsize: Smallest allocatable block size in bytes for storing
        data.
    :ivar int clone_alignment: Expected alignment of arguments for clone and
        deduplication ioctls.

    .. note::
        An object of this type should be retrieved by calling the
        :func:`~btrfs.ctree.FileSystem.fs_info` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    def __init__(self, buf):
        self.max_id, self.num_devices, fsid_bytes, self.nodesize, self.sectorsize, \
            self.clone_alignment = ioctl_fs_info_args.unpack(buf)
        self.fsid = uuid.UUID(bytes=fsid_bytes)

    def __str__(self):
        return "max_id {0} num_devices {1} fsid {2} nodesize {3} sectorsize {4} " \
            "clone_alignment {5}".format(self.max_id, self.num_devices, self.fsid, self.nodesize,
                                         self.sectorsize, self.clone_alignment)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'nodesize'),
            (btrfs.utils.pretty_size, 'sectorsize'),
            (btrfs.utils.pretty_size, 'clone_alignment'),
        ]


def fs_info(fd):
    """Call the `BTRFS_IOC_FS_INFO` ioctl.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :returns: A :class:`FsInfo` object.

    .. note::
        This function should usually be used implicitly by calling the
        :func:`~btrfs.ctree.FileSystem.fs_info` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    buf = bytearray(ioctl_fs_info_args.size)
    fcntl.ioctl(fd, IOC_FS_INFO, buf)
    return FsInfo(buf)


ioctl_dev_info_args = struct.Struct('=Q16sQQ3032x{0}s'.format(DEVICE_PATH_NAME_MAX))
IOC_DEV_INFO = _IOWR(BTRFS_IOCTL_MAGIC, 30, ioctl_dev_info_args)


class DevInfo(object):
    """Object representation of struct btrfs_ioctl_dev_info_args.

    :ivar int devid: Device ID.
    :ivar uuid.UUID uuid: Device UUID.
    :ivar int bytes_used: Amount of allocated bytes on the device.
    :ivar int total_bytes: Device size in bytes.
    :ivar str path: Path to the device node to access this device directly.

    .. note::
        An object of this type should be retrieved by calling the
        :func:`~btrfs.ctree.FileSystem.dev_info` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    def __init__(self, buf):
        self.devid, uuid_bytes, self.bytes_used, self.total_bytes, path_bytes = \
            ioctl_dev_info_args.unpack(buf)
        self.path = path_bytes.split(b'\0', 1)[0].decode()
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "devid {0} uuid {1} bytes_used {2} total_bytes {3} path {4}".format(
            self.devid, self.uuid, self.bytes_used, self.total_bytes, self.path)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.pretty_size, 'bytes_used'),
            (btrfs.utils.pretty_size, 'total_bytes'),
        ]


def dev_info(fd, devid):
    """Call the `BTRFS_IOC_DEV_INFO` ioctl.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int devid: Device ID of the device to retrieve information about.
    :returns: A :class:`DevInfo` object.

    .. note::
        This function should usually be used implicitly by calling the
        :func:`~btrfs.ctree.FileSystem.dev_info` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    buf = bytearray(ioctl_dev_info_args.size)
    ioctl_dev_info_args.pack_into(buf, 0, devid, b'', 0, 0, b'')
    fcntl.ioctl(fd, IOC_DEV_INFO, buf)
    return DevInfo(buf)


ioctl_get_dev_stats = struct.Struct('=QQQ5Q968x')
IOC_GET_DEV_STATS = _IOWR(BTRFS_IOCTL_MAGIC, 52, ioctl_get_dev_stats)


class DevStats(object):
    """Object representation of struct btrfs_ioctl_get_dev_stats.

    :ivar int devid: Device ID.
    :ivar int write_errs: Amount of write errors.
    :ivar int read_errs: Amount of read errors.
    :ivar int flush_errs: Amount of flush errors.
    :ivar int generation_errs: Amount of metadata tree generation mismatch
        errors.
    :ivar int corruption_errs: Amount of checksum failures.

    .. note::
        An object of this type should be retrieved by calling the
        :func:`~btrfs.ctree.FileSystem.dev_stats` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    def __init__(self, buf):
        self.devid, self.nr_items, self.flags, self.write_errs, self.read_errs, \
            self.flush_errs, self.corruption_errs, self.generation_errs = \
            ioctl_get_dev_stats.unpack_from(buf)

    @property
    def counters(self):
        return {
            'write_errs': self.write_errs,
            'read_errs': self.read_errs,
            'flush_errs': self.flush_errs,
            'corruption_errs': self.corruption_errs,
            'generation_errs': self.generation_errs,
        }

    def __str__(self):
        return "devid {0} write_errs {1} read_errs {2} flush_errs {3} corruption_errs {4} " \
            "generation_errs {5}".format(self.devid, self.write_errs, self.read_errs,
                                         self.flush_errs, self.corruption_errs,
                                         self.generation_errs)


def dev_stats(fd, devid, reset=False):
    """Call the `BTRFS_IOC_DEV_STATS` ioctl.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int devid: Device ID of the device to retrieve information about.
    :param bool reset: If true, counters are reset to zero.
    :returns: A :class:`DevStats` object.

    .. note::
        This function should usually be used implicitly by calling the
        :func:`~btrfs.ctree.FileSystem.dev_stats` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    buf = bytearray(ioctl_get_dev_stats.size)
    ioctl_get_dev_stats.pack_into(buf, 0, devid, 5, int(reset), 0, 0, 0, 0, 0)
    fcntl.ioctl(fd, IOC_GET_DEV_STATS, buf)
    return DevStats(buf)


ioctl_space_args = struct.Struct('=2Q')
ioctl_space_info = struct.Struct('=3Q')
IOC_SPACE_INFO = _IOWR(BTRFS_IOCTL_MAGIC, 20, ioctl_space_args)
#: Object representation of struct `btrfs_ioctl_space_args`.
SpaceArgs = namedtuple('SpaceArgs', ['space_slots', 'total_spaces'])


class SpaceInfo(object):
    """Object representation of struct btrfs_ioctl_space_info.

    In btrfs terminology, a 'space' is the collection of all block groups that
    have identical type and profile flags. For example, Metadata, DUP is a
    'space'.

    :ivar int flags: Block group type and profile, e.g. `Data, RAID1`.
    :ivar int total_bytes: Total amount of allocated bytes for this space.
    :ivar int used_bytes: Total amount of bytes used.

    .. note::
        A list of objects of this type should be retrieved by calling the
        :func:`~btrfs.ctree.FileSystem.space_info` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    def __init__(self, buf, pos):
        self.flags, self.total_bytes, self.used_bytes = ioctl_space_info.unpack_from(buf, pos)
        self._type = self.flags & \
            (btrfs.ctree.BLOCK_GROUP_TYPE_MASK | btrfs.ctree.SPACE_INFO_GLOBAL_RSV)
        self._profile = self.flags & btrfs.ctree.BLOCK_GROUP_PROFILE_MASK

    @property
    def type(self):
        """Only block group type, e.g. `Data`, from flags."""
        return self._type

    @property
    def profile(self):
        """Only block group profile, e.g. `RAID1`, from flags."""
        return self._profile

    def __str__(self):
        return "{}: total={}, used={}".format(
            self.flags_str, self.total_bytes_str, self.used_bytes_str)

    @staticmethod
    def _pretty_properties():
        return [
            (btrfs.utils.space_flags_description, 'flags'),
            (btrfs.utils.space_type_description, 'type'),
            (btrfs.utils.space_profile_description, 'profile'),
            (btrfs.utils.pretty_size, 'total_bytes'),
            (btrfs.utils.pretty_size, 'used_bytes'),
        ]


def _space_args(fd):
    buf = bytearray(ioctl_space_args.size)
    fcntl.ioctl(fd, IOC_SPACE_INFO, buf)
    return SpaceArgs(*ioctl_space_args.unpack(buf))


def space_info(fd):
    """Call the `BTRFS_IOC_SPACE_INFO` ioctl.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :returns: A list of :class:`SpaceInfo` objects.

    .. note::
        This function should usually be used implicitly by calling the
        :func:`~btrfs.ctree.FileSystem.space_info` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    args = _space_args(fd)
    buf_size = ioctl_space_args.size + ioctl_space_info.size * args.total_spaces
    buf = bytearray(buf_size)
    ioctl_space_args.pack_into(buf, 0, args.total_spaces, 0)
    fcntl.ioctl(fd, IOC_SPACE_INFO, buf)
    return [SpaceInfo(buf, pos)
            for pos in range(ioctl_space_args.size, buf_size, ioctl_space_info.size)]


ioctl_search_key = struct.Struct('=Q6QLLL4x32x')
ioctl_search_args = struct.Struct('{0}{1}x'.format(
    btrfs.ctree._struct_format(ioctl_search_key), 4096 - ioctl_search_key.size))
ioctl_search_header = struct.Struct('=3Q2L')
IOC_TREE_SEARCH = _IOWR(BTRFS_IOCTL_MAGIC, 17, ioctl_search_args)
#: Object representation of struct `btrfs_ioctl_search_header`.
SearchHeader = namedtuple('SearchHeader', ['transid', 'objectid', 'offset', 'type', 'len'])


def search(fd, tree, min_key=None, max_key=None,
           min_transid=0, max_transid=ULLONG_MAX,
           nr_items=None):
    """Call the `BTRFS_IOC_TREE_SEARCH` ioctl.

    The `TREE_SEARCH` ioctl allow us to directly read btrfs metadata.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int tree: The tree we're searching in. 1 is the tree of tree roots,
        2 is the extent tree, etc... A special tree_id value of 0 will cause a
        search in the subvolume tree that the inode which is passed to the
        ioctl is part of.
    :param btrfs.ctree.Key min_key: Minimum key value for items to return.
    :param btrfs.ctree.Key max_key: Maximum key value for items to return.
    :param int min_transid: Minimum transaction id for the metadata leaf to
        have items included. Defaults to 0.
    :param int max_transid: Maximum transaction id for the metadata leaf to
        have items included. Defaults to 2**64-1.
    :param int nr_items: Maximum amount of items to fetch. Defaults to no
        limit.

    :returns: An iterator over search results, containing a search header and
        the item data per item.
    :rtype: Iterator[Tuple[:class:`SearchHeader`, :class:`memoryview`]]
    """
    return _search(fd, tree, min_key, max_key, min_transid, max_transid,
                   nr_items, _v2=False)


_ioctl_search_args_v2 = [
    ioctl_search_key,
    struct.Struct('=Q')
]
ioctl_search_args_v2 = struct.Struct('=' + ''.join([btrfs.ctree._struct_format(s)[1:]
                                                    for s in _ioctl_search_args_v2]))
IOC_TREE_SEARCH_V2 = _IOWR(BTRFS_IOCTL_MAGIC, 17, ioctl_search_args_v2)


def search_v2(fd, tree, min_key=None, max_key=None,
              min_transid=0, max_transid=ULLONG_MAX,
              nr_items=None, buf_size=16384):
    """Call the `BTRFS_IOC_TREE_SEARCH_V2` ioctl.

    The `TREE_SEARCH_V2` ioctl allow us to directly read btrfs metadata.

    Unlike `TREE_SEARCH`, it allows to use a bigger buffer than 4096 bytes for
    results. This makes it possible to retrieve individual metadata items that
    are bigger than 4kiB, or get more results from a single lookup for
    efficiency reasons.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int tree: The tree we're searching in. 1 is the tree of tree roots,
        2 is the extent tree, etc... A special tree_id value of 0 will cause a
        search in the subvolume tree that the inode which is passed to the
        ioctl is part of.
    :param btrfs.ctree.Key min_key: Minimum key value for items to return.
    :param btrfs.ctree.Key max_key: Maximum key value for items to return.
    :param int min_transid: Minimum transaction id for the metadata leaf to
        have items included. Defaults to 0.
    :param int max_transid: Maximum transaction id for the metadata leaf to
        have items included. Defaults to 2**64-1.
    :param int nr_items: Maximum amount of items to fetch. Defaults to no
        limit.
    :param int buf_size: Buffer size in bytes that will be used for search
        results.

    :returns: An iterator over search results, containing a search header and
        the item data per item.
    :rtype: Iterator[Tuple[:class:`SearchHeader`, :class:`memoryview`]]
    """
    return _search(fd, tree, min_key, max_key, min_transid, max_transid,
                   nr_items, buf_size, _v2=True)


def _search(fd, tree, min_key=None, max_key=None,
            min_transid=0, max_transid=ULLONG_MAX,
            nr_items=None, buf_size=None, _v2=True):
    if min_key is None:
        min_key = btrfs.ctree.Key(0, 0, 0)
    if max_key is None:
        max_key = btrfs.ctree.Key(ULLONG_MAX, 255, ULLONG_MAX)
    if nr_items is not None:
        wanted_nr_items = nr_items
        result_nr_items = -1
    else:
        wanted_nr_items = ULONG_MAX
    while True:
        if _v2:
            buf = bytearray(ioctl_search_args_v2.size + buf_size)
        else:
            buf = bytearray(4096)
        buf_view = memoryview(buf)
        pos = 0
        ioctl_search_key.pack_into(buf, pos, tree,
                                   min_key.objectid, max_key.objectid,
                                   min_key.offset, max_key.offset,
                                   min_transid, max_transid,
                                   min_key.type, max_key.type,
                                   wanted_nr_items)
        pos += ioctl_search_key.size
        if _v2:
            _ioctl_search_args_v2[1].pack_into(buf, pos, buf_size)
            pos += _ioctl_search_args_v2[1].size
            fcntl.ioctl(fd, IOC_TREE_SEARCH_V2, buf)
        else:
            fcntl.ioctl(fd, IOC_TREE_SEARCH, buf)
        result_nr_items = ioctl_search_key.unpack_from(buf, 0)[9]
        if result_nr_items > 0:
            for i in range(result_nr_items):
                header = SearchHeader(*ioctl_search_header.unpack_from(buf, pos))
                pos += ioctl_search_header.size
                yield header, buf_view[pos:pos+header.len]
                if nr_items is not None:
                    wanted_nr_items -= 1
                    if wanted_nr_items == 0:
                        return
                pos += header.len
            min_key = btrfs.ctree.Key(header.objectid, header.type, header.offset)
            min_key += 1
        else:
            return
        if min_key > max_key:
            return


data_container = struct.Struct('=LLLL')
ioctl_logical_ino_args = struct.Struct('=QQ32xQ')
IOC_LOGICAL_INO = _IOWR(BTRFS_IOCTL_MAGIC, 36, ioctl_logical_ino_args)
inum_offset_root = struct.Struct('=QQQ')
#: Inode helper object for `LOGICAL_INO` ioctls results.
Inode = namedtuple('Inode', ['inum', 'offset', 'root'])


def logical_to_ino(fd, vaddr, bufsize=4096):
    """Call the `BTRFS_IOC_LOGICAL_INO` ioctl.

    The `LOGICAL_INO` ioctl helps us converting a virtual address into a list
    of inode numbers of files that use the data extent at that specific
    address.

    Example::

        >>> import btrfs
        >>> with btrfs.FileSystem('/') as fs:
        ...     btrfs.ioctl.logical_to_ino(fs.fd, 607096483840)
        ([Inode(inum=4686948, offset=0, root=259),
          Inode(inum=4686948, offset=0, root=2104)], 0)

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int vaddr: Virtual address to search for.
    :param int bufsize: Size in bytes. Default value is 4kiB (4096 bytes).
        Maximum allowed value is 64kiB (65536 bytes).
    :returns: A list of :class:`Inode` objects and the amount of extra bytes
        for the provided buffer that would be needed to be able to return all
        results found.
    :rtype: Tuple[List[:class:`Inode`], int]

    The default buffer size, 4kiB, can store 170 results. The maximum buffer
    size, 64kiB, can store 2730 results. If a large buffer size is needed, then
    use the logical ino v2 ioctl, which was introduced in Linux kernel 4.15.

    Also, if the requested virtual address points to a disk block that is part
    of a larger extent, but there's no inode that references exactly this block
    in the extent, there will be no results. To get a list of inodes that
    reference any block in the extent, use the logical ino v2 ioctl instead,
    while setting the ignore_offset flag.
    """
    return _logical_to_ino(fd, vaddr, bufsize, _v2=False)


ioctl_logical_ino_args_v2 = struct.Struct('=QQ24xQQ')
IOC_LOGICAL_INO_V2 = _IOWR(BTRFS_IOCTL_MAGIC, 59, ioctl_logical_ino_args)
LOGICAL_INO_ARGS_IGNORE_OFFSET = 1 << 0


def logical_to_ino_v2(fd, vaddr, bufsize=4096, ignore_offset=False):
    """Call the `BTRFS_IOC_LOGICAL_INO_V2` ioctl.

    The `LOGICAL_INO_V2` ioctl helps us converting a virtual address into a
    list of inode numbers of files that use the data extent at that specific
    address.

    Example::

        >>> import btrfs
        >>> with btrfs.FileSystem('/') as fs:
        ...     btrfs.ioctl.logical_to_ino_v2(fs.fd, 607096483840)
        ([Inode(inum=4686948, offset=0, root=259),
          Inode(inum=4686948, offset=0, root=2104)], 0)

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int vaddr: Virtual address to search for.
    :param int bufsize: Size in bytes. Default value is 4kiB (4096 bytes).
        Maximum allowed value is 16MiB (16777216 bytes).
    :param bool ignore_offset: If ignore_offset is set to True, the results
        returned will list all inodes that reference any disk block from the
        extent the virtual address is part of.
    :returns: A list of :class:`Inode` objects and the amount of extra bytes
        for the provided buffer that would be needed to be able to return all
        results found.
    :rtype: Tuple[List[:class:`Inode`], int]

    The default buffer size, 4kiB can store 170 results. To get additional
    results, retry the call with a larger buffer, adding the amount of bytes
    that was reported to be additionally needed.
    """
    return _logical_to_ino(fd, vaddr, bufsize, ignore_offset, _v2=True)


def _logical_to_ino(fd, vaddr, bufsize=4096, ignore_offset=False, _v2=True):
    if _v2:
        bufsize = min(bufsize, 16777216)
    else:
        bufsize = min(bufsize, 65536)
    inodes_buf = array.array(u'B', bytearray(bufsize))
    inodes_ptr = inodes_buf.buffer_info()[0]
    args = bytearray(ioctl_logical_ino_args.size)
    if _v2:
        flags = 0
        if ignore_offset:
            flags |= LOGICAL_INO_ARGS_IGNORE_OFFSET
        ioctl_logical_ino_args_v2.pack_into(args, 0, vaddr, bufsize, flags, inodes_ptr)
        fcntl.ioctl(fd, IOC_LOGICAL_INO_V2, args)
    else:
        ioctl_logical_ino_args.pack_into(args, 0, vaddr, bufsize, inodes_ptr)
        fcntl.ioctl(fd, IOC_LOGICAL_INO, args)
    bytes_left, bytes_missing, elem_cnt, elem_missed = data_container.unpack_from(inodes_buf, 0)
    inodes = []
    pos = data_container.size
    for elem in range(int(elem_cnt//3)):
        inodes.append(Inode(*inum_offset_root.unpack_from(inodes_buf, pos)))
        pos += inum_offset_root.size
    return inodes, bytes_missing


INO_LOOKUP_PATH_MAX = 4080
ioctl_ino_lookup_args = struct.Struct('=QQ{}s'.format(INO_LOOKUP_PATH_MAX))
IOC_INO_LOOKUP = _IOWR(BTRFS_IOCTL_MAGIC, 18, ioctl_ino_lookup_args)
#: Helper object for `INO_LOOKUP` ioctls results.
InoLookupResult = namedtuple('InoLookupResult', ['treeid', 'name_bytes'])


def ino_lookup(fd, treeid=0, objectid=btrfs.ctree.FIRST_FREE_OBJECTID):
    """Call the `BTRFS_IOC_INO_LOOKUP` ioctl.

    The `INO_LOOKUP` ioctl returns the containing subvolume tree id and the
    relative path inside that subvolume of the first listed path for an inode
    number.

    Example::

        >>> import btrfs
        >>> import os
        >>> fd = os.open('/', os.O_RDONLY)
        >>> btrfs.ioctl.ino_lookup(fd, objectid=4686948)
        InoLookupResult(treeid=259, name_bytes=b'bin/bash/')

    :param int fd: File descriptor pointing to an inode.
    :param int treeid: Subvolume tree to search in, or 0 to use the subvolume
        that contains the inode that fd points to.
    :param int objectid: Inode number to get the path for.

    :returns: An :class:`InoLookupResult` tuple with subvolume tree id and
        filesystem path as bytes.
    :rtype: :class:`InoLookupResult`
    """
    args = bytearray(ioctl_ino_lookup_args.size)
    ioctl_ino_lookup_args.pack_into(args, 0, treeid, objectid, b'')
    fcntl.ioctl(fd, IOC_INO_LOOKUP, args)
    treeid, _, name_bytes = ioctl_ino_lookup_args.unpack_from(args, 0)
    return InoLookupResult(treeid, name_bytes.split(b'\0', 1)[0])


BALANCE_ARGS_PROFILES = 1 << 0
BALANCE_ARGS_USAGE = 1 << 1
BALANCE_ARGS_DEVID = 1 << 2
BALANCE_ARGS_DRANGE = 1 << 3
BALANCE_ARGS_VRANGE = 1 << 4
BALANCE_ARGS_LIMIT = 1 << 5
BALANCE_ARGS_LIMIT_RANGE = 1 << 6
BALANCE_ARGS_STRIPES_RANGE = 1 << 7
BALANCE_ARGS_CONVERT = 1 << 8
BALANCE_ARGS_SOFT = 1 << 9
BALANCE_ARGS_USAGE_RANGE = 1 << 10

_balance_args_flags_str_map = {
    BALANCE_ARGS_PROFILES: 'PROFILES',
    BALANCE_ARGS_USAGE: 'USAGE',
    BALANCE_ARGS_DEVID: 'DEVID',
    BALANCE_ARGS_DRANGE: 'DRANGE',
    BALANCE_ARGS_VRANGE: 'VRANGE',
    BALANCE_ARGS_LIMIT: 'LIMIT',
    BALANCE_ARGS_LIMIT_RANGE: 'LIMIT_RANGE',
    BALANCE_ARGS_STRIPES_RANGE: 'STRIPES_RANGE',
    BALANCE_ARGS_CONVERT: 'CONVERT',
    BALANCE_ARGS_SOFT: 'SOFT',
    BALANCE_ARGS_USAGE_RANGE: 'USAGE_RANGE',
}


def _balance_args_flags_str(flags):
    return btrfs.utils.flags_str(flags, _balance_args_flags_str_map)


def _balance_args_profiles_str(profiles):
    return btrfs.utils.flags_str(profiles, btrfs.ctree._balance_args_profiles_str_map)


class BalanceArgs(object):
    """Object representation of struct `btrfs_balance_args`.

    When calling the balance ioctl, we have to pass filters that define which
    subset of block groups in the filesystem we want to rewrite.

    Example::

        >>> args = btrfs.ioctl.BalanceArgs(vstart=115993477120,
                vend=191155404800, limit_min=2, limit_max=2)
        >>> print(args)
        flags(VRANGE|LIMIT_RANGE) vrange=115993477120..191155404800, limit=2..2
        >>> args
        BalanceArgs(vstart=115993477120, vend=191155404800, limit_min=2,
                    limit_max=2)

    When defining multiple filter criteria, they all have to match for a block
    group to be processed by the balance run.

    The balance ioctl accepts three of these BalanceArgs at the same time,
    one for data, one for metadata and one for the system type.

    :param int profiles: Match block groups having either of the given
        profiles. A single value of or-ed together block group profile
        constants.  E.g. `BLOCK_GROUP_RAID1 | BLOCK_GROUP_DUP`.  Note that
        there is no `BLOCK_GROUP_SINGLE`, since the single profile uses the
        value zero. For choosing the single profile here, use the
        `AVAIL_ALLOC_BIT_SINGLE` constant that is available in the
        `btrfs.ctree` module.
    :param int usage_min: Match block groups with usage equal to or above
        the given percentage.
    :param int usage_max: Match block groups with usage under the given
        percentage.
    :param int devid: Match block groups whose related Chunk object has a
        Stripe object using physical space on this device.
    :param int pstart: Match block groups using physical bytes on a device on
        or after the given start address. Use this in combination with the
        `devid` option.
    :param int pend: Match block groups using physical bytes on a device before
        the given end address. Use this in combination with the `devid` option.
    :param int vstart: Match block groups that overlap with the given virtual
        address, or a higher address.
    :param int vend: Match block groups that overlap with a virtual address
        before the given address.
    :param int target: Target block group profile to convert to.
    :param int limit_min: Try to process at least this amount of block groups.
    :param int limit_max: Process at most this amount of block groups.
    :param int stripes_min: Match block groups which have an associated Chunk
        object that has at least this amount of related Stripe objects.
    :param int stripes_max: Match block groups which have an associated Chunk
        object that has at most this amount of related Stripe objects.
    :param bool soft: When set, skip matching block groups that already have
        the target profile when doing a conversion.

    The arguments given when creating a BalanceArgs object are available as
    attributes on the resulting object, together with a flags field:

    :ivar int flags: Flags denoting which filter options are set.

    The flags are an or-ed combination of one or more of the following values
    (available as attribute of this module):

    - BALANCE_ARGS_PROFILES
    - BALANCE_ARGS_USAGE
    - BALANCE_ARGS_DEVID
    - BALANCE_ARGS_DRANGE
    - BALANCE_ARGS_VRANGE
    - BALANCE_ARGS_LIMIT
    - BALANCE_ARGS_LIMIT_RANGE
    - BALANCE_ARGS_STRIPES_RANGE
    - BALANCE_ARGS_CONVERT
    - BALANCE_ARGS_SOFT
    - BALANCE_ARGS_USAGE_RANGE

    .. note::
        This class does not implement single usage and limit values, and is
        thus incompatible with a Linux kernel older than v4.4.
    """
    def __init__(self, profiles=None, usage_min=None, usage_max=None,
                 devid=None, pstart=None, pend=None, vstart=None, vend=None,
                 target=None, limit_min=None, limit_max=None,
                 stripes_min=None, stripes_max=None, soft=False):
        self.flags = 0

        if profiles is not None:
            self.flags |= BALANCE_ARGS_PROFILES
            self.profiles = profiles
        else:
            self.profiles = 0

        if usage_min is not None:
            self.flags |= BALANCE_ARGS_USAGE_RANGE
            self.usage_min = usage_min
        else:
            self.usage_min = 0

        if usage_max is not None:
            self.flags |= BALANCE_ARGS_USAGE_RANGE
            self.usage_max = usage_max
        else:
            self.usage_max = 100

        if devid is not None:
            self.flags |= BALANCE_ARGS_DEVID
            self.devid = devid
            if pstart is not None:
                self.flags |= BALANCE_ARGS_DRANGE
                self.pstart = pstart
            else:
                self.pstart = 0
            if pend is not None:
                self.flags |= BALANCE_ARGS_DRANGE
                self.pend = pend
            else:
                self.pend = ULLONG_MAX
        else:
            self.devid = 0
            self.pstart = 0
            self.pend = ULLONG_MAX

        if vstart is not None:
            self.flags |= BALANCE_ARGS_VRANGE
            self.vstart = vstart
        else:
            self.vstart = 0
        if vend is not None:
            self.flags |= BALANCE_ARGS_VRANGE
            self.vend = vend
        else:
            self.vend = ULLONG_MAX

        if target is not None:
            self.flags |= BALANCE_ARGS_CONVERT
            self.target = target
            if soft:
                self.flags |= BALANCE_ARGS_SOFT
                self.soft = soft
        else:
            self.target = 0

        if limit_min is not None:
            self.flags |= BALANCE_ARGS_LIMIT_RANGE
            self.limit_min = limit_min
        else:
            self.limit_min = 0

        if limit_max is not None:
            self.flags |= BALANCE_ARGS_LIMIT_RANGE
            self.limit_max = limit_max
        else:
            self.limit_max = ULONG_MAX

        if stripes_min is not None:
            self.flags |= BALANCE_ARGS_STRIPES_RANGE
            self.stripes_min = stripes_min
        else:
            self.stripes_min = 0

        if stripes_max is not None:
            self.flags |= BALANCE_ARGS_STRIPES_RANGE
            self.stripes_max = stripes_max
        else:
            self.stripes_max = ULONG_MAX

    def _for_struct(self):
        return self.profiles, self.usage_min, self.usage_max, self.devid, self.pstart, self.pend, \
            self.vstart, self.vend, self.target, self.flags, self.limit_min, self.limit_max, \
            self.stripes_min, self.stripes_max

    def __repr__(self):
        opts = []
        if self.flags & BALANCE_ARGS_PROFILES:
            opts.append("profiles={:#x}".format(self.profiles))
        if self.flags & BALANCE_ARGS_USAGE_RANGE:
            opts.append("usage_min={}, usage_max={}".format(self.usage_min, self.usage_max))
        if self.flags & BALANCE_ARGS_DEVID:
            opts.append("devid={}".format(self.devid))
        if self.flags & BALANCE_ARGS_DRANGE:
            opts.append("pstart={}, pend={}".format(self.pstart, self.pend))
        if self.flags & BALANCE_ARGS_VRANGE:
            opts.append("vstart={}, vend={}".format(self.vstart, self.vend))
        if self.flags & BALANCE_ARGS_CONVERT:
            opts.append("target={:#x}".format(self.target))
        if self.flags & BALANCE_ARGS_LIMIT_RANGE:
            opts.append("limit_min={}, limit_max={}".format(self.limit_min, self.limit_max))
        if self.flags & BALANCE_ARGS_STRIPES_RANGE:
            opts.append("stripes_min={}, stripes_max={}".format(
                self.stripes_min, self.stripes_max))
        if self.flags & BALANCE_ARGS_SOFT:
            opts.append("soft=True")
        return "BalanceArgs({})".format(', '.join(opts))

    def __str__(self):
        opts = []
        if self.flags & BALANCE_ARGS_PROFILES:
            opts.append("profiles={}".format(self.profiles_str))
        if self.flags & BALANCE_ARGS_USAGE_RANGE:
            opts.append("usage={}..{}".format(self.usage_min, self.usage_max))
        if self.flags & BALANCE_ARGS_DEVID:
            opts.append("devid={}".format(self.devid))
        if self.flags & BALANCE_ARGS_DRANGE:
            opts.append("drange={}..{}".format(self.pstart, self.pend))
        if self.flags & BALANCE_ARGS_VRANGE:
            opts.append("vrange={}..{}".format(self.vstart, self.vend))
        if self.flags & BALANCE_ARGS_CONVERT:
            opts.append("target={}".format(self.target_str))
        if self.flags & BALANCE_ARGS_LIMIT_RANGE:
            opts.append("limit={}..{}".format(self.limit_min, self.limit_max))
        if self.flags & BALANCE_ARGS_STRIPES_RANGE:
            opts.append("stripes={}..{}".format(self.stripes_min, self.stripes_max))
        if self.flags & BALANCE_ARGS_SOFT:
            opts.append("soft")
        return "flags({}) {}".format(self.flags_str, ', '.join(opts))

    @staticmethod
    def _pretty_properties():
        return [
            (_balance_args_flags_str, 'flags'),
            (_balance_args_profiles_str, 'profiles'),
            (_balance_args_profiles_str, 'target'),
        ]


BALANCE_DATA = 1 << 0
BALANCE_SYSTEM = 1 << 1
BALANCE_METADATA = 1 << 2
BALANCE_TYPE_MASK = BALANCE_DATA | BALANCE_SYSTEM | BALANCE_METADATA
BALANCE_FORCE = 1 << 3
BALANCE_RESUME = 1 << 4

BALANCE_STATE_RUNNING = 1 << 0
BALANCE_STATE_PAUSE_REQ = 1 << 1
BALANCE_STATE_CANCEL_REQ = 1 << 2

_balance_state_str_map = {
    BALANCE_STATE_RUNNING: 'RUNNING',
    BALANCE_STATE_PAUSE_REQ: 'PAUSE_REQ',
    BALANCE_STATE_CANCEL_REQ: 'CANCEL_REQ',
}


def _balance_state_str(state):
    return btrfs.utils.flags_str(state, _balance_state_str_map)


# These should actually be without leading underscore, but we also have a
# function named balance_progress...
_balance_args = struct.Struct('=QLL7Q4L48x')
_balance_progress = struct.Struct('=3Q')


class BalanceProgress(object):
    """Object representation of struct `btrfs_balance_progress`.

    :ivar int state: current state of a running balance operation.

    When a progress object is returned by :func:`~btrfs.ioctl.balance_v2` after
    a successful uninterrupted run, the value of state is 0.

    When obtaining a progress object by calling
    :func:`~btrfs.ioctl.balance_progress`, the possible state values (available
    as attribute of this module) are:

    - `BALANCE_STATE_RUNNING`: Balance is running.
    - `BALANCE_STATE_PAUSE_REQ`: Balance is running, but a pause is requested.
    - `BALANCE_STATE_CANCEL_REQ`: Balance is running, but cancel is requested.

    :ivar int expected: Estimated number of block groups that will be relocated
        to fulfill the request.
    :ivar int considered: Number of block groups that were inspected to see if
        they match the requested filters.
    :ivar int completed: Number of block groups relocated so far.
    """
    def __init__(self, state, expected, considered, completed):
        self.state = state
        self.expected = expected
        self.considered = considered
        self.completed = completed

    def __repr__(self):
        return "BalanceProgress(state={self.state:#x}, expected={self.expected}, " \
            "considered={self.considered}, completed={self.completed})".format(self=self)

    def __str__(self):
        return "state {self.state_str} expected {self.expected} considered {self.considered} " \
            "completed {self.completed}".format(self=self)

    @staticmethod
    def _pretty_properties():
        return [
            (_balance_state_str, 'state'),
        ]


_ioctl_balance_args = [
    struct.Struct('=Q'),  # 0 - flags - in/out
    struct.Struct('=Q'),  # 1 - state - out
    _balance_args,  # 2 - data - in/out
    _balance_args,  # 3 - meta - in/out
    _balance_args,  # 4 - sys - in/out
    _balance_progress,  # 5 - stat - out
    struct.Struct('=576x')
]
ioctl_balance_args = struct.Struct('=' + ''.join([btrfs.ctree._struct_format(s)[1:]
                                                  for s in _ioctl_balance_args]))
IOC_BALANCE_V2 = _IOWR(BTRFS_IOCTL_MAGIC, 32, ioctl_balance_args)


class BalanceError(Exception):
    """Exception class for balance functionality.

    A :class:`BalanceError` can be thrown by any of the balance related
    functions in this module.

    :ivar int state: One of the balance state values, see below. This field is
        only set to a non-zero value when the error is raised by the
        :func:`balance_v2` function.
    :ivar int errno: An errno errorcode that was returned when executing the
        ioctl call in one of the balance related functions.
    :ivar str msg: A message describing the error condition.

    Refer to the docucumentation of the different functions who can raise this
    error for more information about combinations of the state and errno
    numbers that can be expected, and about what they mean.
    """
    def __init__(self, state, msg):
        self.state = state
        self.msg = msg

    @property
    def errno(self):
        return self.__context__.errno

    def __str__(self):
        return self.msg


def balance_v2(fd, data_args=None, meta_args=None, sys_args=None, force=False, resume=False):
    """Call the `BTRFS_IOC_BALANCE_V2` ioctl.

    Ask the kernel to relocate block groups.

    Example::

        >>> import btrfs
        >>> args = btrfs.ioctl.BalanceArgs(vstart=115993477120,
                vend=191155404800, limit_min=2, limit_max=2)
        >>> with btrfs.FileSystem('/') as fs:
        ...     btrfs.ioctl.balance_v2(fs.fd, data_args=args)
        ...
        BalanceProgress(state=0x0, expected=2, considered=466, completed=2)

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param BalanceArgs data_args: Filters for Data type block groups.
    :param BalanceArgs meta_args: Filters for Metadata type block groups.
    :param BalanceArgs sys_args: Filters for System type block groups.
    :param bool force: When True, this allows converting to a profile with less
        redundancy.
    :param bool resume: When True, all args are ignored and we ask the kernel
        to resume a previous balance operation.

    :returns: A :class:`BalanceProgress` object, describing the end result.
    :rtype: :class:`BalanceProgress`

    :raises: :class:`BalanceError`, in case the balance operation does not exit
        in a clean way. Possible reasons include pausing or canceling the
        balance operation by a separate call to
        :func:`~btrfs.ioctl.balance_ctl`, or having another balance operation
        already running.

    When a :class:`BalanceError` is raised, the following combinations of state
    and errno attributes can be expected:

    - errno `ECANCELED`, state `BALANCE_STATE_PAUSE_REQ`: The balance operation
      was paused because of a user request.
    - errno `ECANCELED`, state `BALANCE_STATE_CANCEL_REQ`: The balance
      operation was aborted because of a user request.
    - errno `ENOTCONN`: A resume was requested, but there was no previously
      paused balance operation.
    - errno `EINPROGRESS`: A resume or start was requested, but there is
      already a balance operation in progress.
    """
    args = bytearray(ioctl_balance_args.size)
    if resume:
        _ioctl_balance_args[0].pack_into(args, 0, BALANCE_RESUME)
    else:
        flags = 0
        pos = _ioctl_balance_args[0].size
        pos += _ioctl_balance_args[1].size
        if data_args is not None:
            flags |= BALANCE_DATA
            _balance_args.pack_into(args, pos, *data_args._for_struct())
        pos += _balance_args.size
        if meta_args is not None:
            flags |= BALANCE_METADATA
            _balance_args.pack_into(args, pos, *meta_args._for_struct())
        pos += _balance_args.size
        if sys_args is not None:
            flags |= BALANCE_SYSTEM
            _balance_args.pack_into(args, pos, *sys_args._for_struct())
        if force:
            flags |= BALANCE_FORCE
        _ioctl_balance_args[0].pack_into(args, 0, flags)
    try:
        fcntl.ioctl(fd, IOC_BALANCE_V2, args)
    except OSError as oserror:
        pos = _ioctl_balance_args[0].size
        state, = _ioctl_balance_args[1].unpack_from(args, pos)
        errorcode = errno.errorcode[oserror.errno]
        if oserror.errno == errno.ECANCELED:
            if state & BALANCE_STATE_PAUSE_REQ:
                msg = "Balance paused by user"
            if state & BALANCE_STATE_CANCEL_REQ:
                msg = "Balance canceled by user"
        elif oserror.errno == errno.ENOTCONN and resume:
            msg = "Balance resume failed: Not in progress ({})".format(errorcode)
        elif oserror.errno == errno.EINPROGRESS:
            if resume:
                msg = "Balance resume failed: Already running ({})".format(errorcode)
            else:
                msg = "Balance start failed: Already in progress ({})".format(errorcode)
        else:
            msg = "Error during balancing, there may be more info in dmesg: {}, " \
                "state {}".format(errorcode, _balance_state_str(state))
        raise BalanceError(state, msg) from None
    pos = _ioctl_balance_args[0].size
    state, = _ioctl_balance_args[1].unpack_from(args, pos)
    pos = sum(x.size for x in _ioctl_balance_args[:5])
    return BalanceProgress(state, *_balance_progress.unpack_from(args, pos))


BALANCE_CTL_PAUSE = 1
BALANCE_CTL_CANCEL = 2
ioctl_balance_ctl_int = struct.Struct('=i')
IOC_BALANCE_CTL = _IOW(BTRFS_IOCTL_MAGIC, 33, ioctl_balance_ctl_int)


def balance_ctl(fd, cmd):
    """Call the `BTRFS_IOC_BALANCE_CTL` ioctl.

    Ask the kernel to pause or cancel a running balance operation.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :param int cmd: Balance control command.

    Available commands (available as attribute of this module) are:

    - `BALANCE_CTL_PAUSE`
    - `BALANCE_CTL_CANCEL`

    :raises: :class:`BalanceError` if there is no balance in progress, or if
        pausing or cancelling it failed.

    When a :class:`BalanceError` is raised, the following values for the errno
    attribute can be expected:

    - errno `ENOTCONN`: There is no balance operation in progress, so it cannot
      be paused or cancelled.
    """
    try:
        fcntl.ioctl(fd, IOC_BALANCE_CTL, cmd)
    except OSError as oserror:
        errorcode = errno.errorcode[oserror.errno]
        if cmd == BALANCE_CTL_PAUSE:
            if oserror.errno == errno.ENOTCONN:
                msg = "Balance pause failed: Not in progress ({})".format(errorcode)
            else:
                msg = "Balance pause failed ({})".format(errorcode)
        elif cmd == BALANCE_CTL_CANCEL:
            if oserror.errno == errno.ENOTCONN:
                msg = "Balance cancel failed: Not in progress ({})".format(errorcode)
            else:
                msg = "Balance cancel failed ({})".format(errorcode)
        raise BalanceError(0, msg) from None


IOC_BALANCE_PROGRESS = _IOR(BTRFS_IOCTL_MAGIC, 34, ioctl_balance_args)


def balance_progress(fd):
    """Call the `BTRFS_IOC_BALANCE_PROGRESS` ioctl.

    Ask the kernel about progress of a running balance operation.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :returns: A :class:`BalanceProgress` object, describing the current state
        of the balance operation.
    :rtype: :class:`BalanceProgress`

    :raises: :class:`BalanceError` if there is no balance in progress, or if
        inquiring about the progress failed.

    When a :class:`BalanceError` is raised, the following values for the errno
    attribute can be expected:

    - errno `ENOTCONN`: There is no balance operation in progress.
    """
    args = bytearray(ioctl_balance_args.size)
    try:
        fcntl.ioctl(fd, IOC_BALANCE_PROGRESS, args)
    except OSError as oserror:
        pos = _ioctl_balance_args[0].size
        state, = _ioctl_balance_args[1].unpack_from(args, pos)
        errorcode = errno.errorcode[oserror.errno]
        if oserror.errno == errno.ENOTCONN:
            msg = "No balance found ({})".format(errorcode)
        else:
            msg = "Balance progress failed ({})".format(errorcode)
        raise BalanceError(0, msg) from None
    pos = _ioctl_balance_args[0].size
    state, = _ioctl_balance_args[1].unpack_from(args, pos)
    pos = sum(x.size for x in _ioctl_balance_args[:5])
    return BalanceProgress(state, *_balance_progress.unpack_from(args, pos))


ioctl_received_subvol_args = struct.Struct('=16sQQQLQLQ128x')
_ioctl_received_subvol_args_in = struct.Struct('=16sQ8xQL148x')
_ioctl_received_subvol_args_out_up_to_rtime = struct.Struct('=24xQ12x')
IOC_SET_RECEIVED_SUBVOL = _IOWR(BTRFS_IOCTL_MAGIC, 37, ioctl_received_subvol_args)


def set_received_subvol(fd, received_uuid, stransid, stime):
    """Call the `BTRFS_IOC_SET_RECEIVED_SUBVOL` ioctl.

    This function allows setting information about a sent subvolume after a
    receive operation.

    Using this functionality it is possible to manually change relationships
    between sent and received subvolumes, removing safeguards and tricking
    btrfs into accepting certain incremental send and receive operations.

    Use with caution, as it is also possible to cause subsequent `btrfs
    receive` to try doing wildly invalid things as result.

    :param int fd: An open file descriptor to the subvolume root directory
        (inode 256).
    :param uuid.UUID uuid: The uuid (a python uuid object) we want to have set
        as received_uuid.
    :param int stransid: Generation of the subvolume that was sent.
    :param btrfs.ctree.TimeSpec stime: Time when the subvolume was sent.

    Note that the stime field is not set at all by `btrfs receive`.
    """
    args = bytearray(_ioctl_received_subvol_args_in.size)
    _ioctl_received_subvol_args_in.pack_into(args, 0, received_uuid.bytes, stransid,
                                             stime.sec, stime.nsec)
    fcntl.ioctl(fd, IOC_SET_RECEIVED_SUBVOL, args)
    rtransid, = _ioctl_received_subvol_args_out_up_to_rtime.unpack_from(args, 0)
    pos = _ioctl_received_subvol_args_out_up_to_rtime.size
    rtime = btrfs.ctree.TimeSpec(args[pos:pos+btrfs.ctree.TimeSpec._timespec.size])
    return rtransid, rtime


IOC_SYNC = _IO(BTRFS_IOCTL_MAGIC, 8)


def sync(fd):
    """Call the `BTRFS_IOC_SYNC` ioctl.

    The sync ioctl triggers delayed allocations, a btrfs transaction commit and
    the cleaner kthread.

    :param int fd: Open file descriptor to any inode in the filesystem.

    .. note::
        This function should usually be used implicitly by calling the
        :func:`~btrfs.ctree.FileSystem.sync` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    fcntl.ioctl(fd, IOC_SYNC)


file_dedupe_range_info = struct.Struct('=qQQl4x')
file_dedupe_range = struct.Struct('=QQH6x')

FIDEDUPERANGE = _IOWR(BTRFS_IOCTL_MAGIC, 54, file_dedupe_range)

FILE_DEDUPE_RANGE_SAME = 0
FILE_DEDUPE_RANGE_DIFFERS = 1


class FileDedupeRangeInfo(object):
    """Object representation of struct `file_dedupe_range_info`.

    :param int dest_fd: An open file descriptor to a destination file which
        should get content deduped.
    :param int dest_offset: Byte offset in the destination file from where the
        dedupe operation should happen.

    After calling :func:`fideduperange`, the object will contain return values
    of the dedupe operation for this destination file:

    :ivar int bytes_deduped: Amount of actual bytes at the given offset that
        could be deduped.
    :ivar int status: One of the two status codes mentioned below (available as
        attribute of this module) or a negative number, which means it's a
        standard errno integer value from the kernel.

    - `FILE_DEDUPE_RANGE_SAME`: The source range provided was identical to the
      data at the destination offset and could be deduped.
    - `FILE_DEDUPE_RANGE_DIFFERS`: Data in the destination was not matching,
      and the range could not be deduped.
    """
    def __init__(self, dest_fd, dest_offset):
        self.dest_fd = dest_fd
        self.dest_offset = dest_offset
        self.bytes_deduped = None
        self.status = None

    @property
    def status_str(self):
        """Pretty string representation for the status attribute."""
        if self.status == btrfs.ioctl.FILE_DEDUPE_RANGE_SAME:
            return "RANGE_SAME"
        if self.status == FILE_DEDUPE_RANGE_DIFFERS:
            return "RANGE_DIFFERS"
        return "ERROR {}: {}".format(self.status, os.strerror(-self.status))

    def __str__(self):
        return "dest_fd {self.dest_fd} dest_offset {self.dest_offset} " \
               "bytes_deduped {self.bytes_deduped} status {self.status_str}".format(self=self)


def fideduperange(fd, src_offset, src_length, range_infos):
    """Call the `FIDEDUPERANGE` ioctl.

    :param int fd: Open file descriptor to a source file.
    :param int src_offset: Offset in the source file where the source range
        starts.
    :param int src_length: Length of the source range.
    :param range_infos: Information about offsets in destination files.
    :type range_infos: list of :class:`FileDedupeRangeInfo`
    """
    buf = bytearray(file_dedupe_range.size + file_dedupe_range_info.size * len(range_infos))
    file_dedupe_range.pack_into(buf, 0, src_offset, src_length, len(range_infos))
    pos = file_dedupe_range.size
    for info in range_infos:
        file_dedupe_range_info.pack_into(buf, pos, info.dest_fd, info.dest_offset, 0, 0)
        pos += file_dedupe_range_info.size
    fcntl.ioctl(fd, FIDEDUPERANGE, buf)
    pos = file_dedupe_range.size
    for info in range_infos:
        _, _, bytes_deduped, status = file_dedupe_range_info.unpack_from(buf, pos)
        info.bytes_deduped = bytes_deduped
        info.status = status
        pos += file_dedupe_range_info.size


ioctl_feature_flags = struct.Struct('=QQQ')
IOC_GET_FEATURES = _IOR(BTRFS_IOCTL_MAGIC, 57, ioctl_feature_flags)

_feature_compat_str_map = {
}


def _compat_flags_str(flags):
    return btrfs.utils.flags_str(flags, _feature_compat_str_map)


FEATURE_COMPAT_RO_FREE_SPACE_TREE = 1 << 0
FEATURE_COMPAT_RO_FREE_SPACE_TREE_VALID = 1 << 1

_feature_compat_ro_str_map = {
    FEATURE_COMPAT_RO_FREE_SPACE_TREE: 'free_space_tree',
    FEATURE_COMPAT_RO_FREE_SPACE_TREE_VALID: 'free_space_tree_valid',
}


def _compat_ro_flags_str(flags):
    return btrfs.utils.flags_str(flags, _feature_compat_ro_str_map)


FEATURE_INCOMPAT_MIXED_BACKREF = 1 << 0
FEATURE_INCOMPAT_DEFAULT_SUBVOL = 1 << 1
FEATURE_INCOMPAT_MIXED_GROUPS = 1 << 2
FEATURE_INCOMPAT_COMPRESS_LZO = 1 << 3
FEATURE_INCOMPAT_COMPRESS_ZSTD = 1 << 4
FEATURE_INCOMPAT_BIG_METADATA = 1 << 5
FEATURE_INCOMPAT_EXTENDED_IREF = 1 << 6
FEATURE_INCOMPAT_RAID56 = 1 << 7
FEATURE_INCOMPAT_SKINNY_METADATA = 1 << 8
FEATURE_INCOMPAT_NO_HOLES = 1 << 9

_feature_incompat_str_map = {
    FEATURE_INCOMPAT_MIXED_BACKREF: 'mixed_backref',
    FEATURE_INCOMPAT_DEFAULT_SUBVOL: 'default_subvol',
    FEATURE_INCOMPAT_MIXED_GROUPS: 'mixed_groups',
    FEATURE_INCOMPAT_COMPRESS_LZO: 'compress_lzo',
    FEATURE_INCOMPAT_COMPRESS_ZSTD: 'compress_zstd',
    FEATURE_INCOMPAT_BIG_METADATA: 'big_metadata',
    FEATURE_INCOMPAT_EXTENDED_IREF: 'extended_iref',
    FEATURE_INCOMPAT_RAID56: 'raid56',
    FEATURE_INCOMPAT_SKINNY_METADATA: 'skinny_metadata',
    FEATURE_INCOMPAT_NO_HOLES: 'no_holes',
}


def _incompat_flags_str(flags):
    return btrfs.utils.flags_str(flags, _feature_incompat_str_map)


class FeatureFlags(object):
    """Object representation of struct `btrfs_ioctl_feature_flags`.

    Quoting from linux kernel commit `f2b636e80d`:

    :ivar int compat_flags: These hold the features that are compatible with
        older versions of btrfs.
    :ivar int compat_ro_flags: These flags have features that are compatible
        with older versions of btrfs if the fs is mounted read only.
    :ivar int incompat_flags: This has features that are incompatible with
        older versions of btrfs.

    Compat flags are currently not used.

    Known compat_ro flags (available as attribute of this module) are:

    - FEATURE_COMPAT_RO_FREE_SPACE_TREE
    - FEATURE_COMPAT_RO_FREE_SPACE_TREE_VALID

    Known incompat_flags (available as attribute of this module) are:

    - FEATURE_INCOMPAT_MIXED_BACKREF
    - FEATURE_INCOMPAT_DEFAULT_SUBVOL
    - FEATURE_INCOMPAT_MIXED_GROUPS
    - FEATURE_INCOMPAT_COMPRESS_LZO
    - FEATURE_INCOMPAT_COMPRESS_ZSTD
    - FEATURE_INCOMPAT_BIG_METADATA
    - FEATURE_INCOMPAT_EXTENDED_IREF
    - FEATURE_INCOMPAT_RAID56
    - FEATURE_INCOMPAT_SKINNY_METADATA
    - FEATURE_INCOMPAT_NO_HOLES

    Example::

        >>> import btrfs
        >>> with btrfs.FileSystem('/') as fs:
        ...     features = fs.features()
        ...
        >>> btrfs.utils.pretty_print(features)
        <btrfs.ioctl.FeatureFlags>
        compat_flags: none
        compat_ro_flags: free_space_tree|free_space_tree_valid
        incompat_flags: mixed_backref|default_subvol|compress_lzo|big_metadata|extended_iref
        >>> features.incompat_flags & btrfs.ioctl.FEATURE_INCOMPAT_MIXED_GROUPS
        0
        >>> features.incompat_flags & btrfs.ioctl.FEATURE_COMPAT_RO_FREE_SPACE_TREE
        1

    .. note::
        An object of this type should be retrieved by calling the
        :func:`~btrfs.ctree.FileSystem.features` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    def __init__(self, compat_flags, compat_ro_flags, incompat_flags):
        self.compat_flags = compat_flags
        self.compat_ro_flags = compat_ro_flags
        self.incompat_flags = incompat_flags

    @staticmethod
    def _pretty_properties():
        return [
            (_compat_flags_str, 'compat_flags'),
            (_compat_ro_flags_str, 'compat_ro_flags'),
            (_incompat_flags_str, 'incompat_flags'),
        ]


def get_features(fd):
    """Call the `BTRFS_IOC_GET_FEATURES` ioctl.

    :param int fd: Open file descriptor to any inode in the filesystem.
    :returns: A :class:`FeatureFlags` object.

    .. note::
        This function should usually be used implicitly by calling the
        :func:`~btrfs.ctree.FileSystem.features` function on a
        :class:`btrfs.ctree.FileSystem` object.
    """
    buf = bytearray(ioctl_feature_flags.size)
    fcntl.ioctl(fd, IOC_GET_FEATURES, buf)
    compat_flags, compat_ro_flags, incompat_flags = ioctl_feature_flags.unpack(buf)
    return FeatureFlags(compat_flags, compat_ro_flags, incompat_flags)
