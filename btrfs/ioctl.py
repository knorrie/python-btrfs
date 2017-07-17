# Copyright (C) 2016-2017 Hans van Kranenburg <hans@knorrie.org>
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
import array
import errno
import fcntl
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

from btrfs.ctree import BLOCK_GROUP_TYPE_MASK, SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_PROFILE_MASK  # noqa
from btrfs.ctree import FIRST_FREE_OBJECTID  # noqa
import btrfs.ctree  # noqa


ioctl_fs_info_args = struct.Struct('=QQ16sLLL980x')
IOC_FS_INFO = _IOR(BTRFS_IOCTL_MAGIC, 31, ioctl_fs_info_args)


class FsInfo(object):
    def __init__(self, buf):
        self.max_id, self.num_devices, fsid_bytes, self.nodesize, self.sectorsize, \
            self.clone_alignment = ioctl_fs_info_args.unpack(buf)
        self.fsid = uuid.UUID(bytes=fsid_bytes)

    def __str__(self):
        return "max_id {0} num_devices {1} fsid {2} nodesize {3} sectorsize {4} " \
            "clone_alignment {5}".format(self.max_id, self.num_devices, self.fsid, self.nodesize,
                                         self.sectorsize, self.clone_alignment)


def fs_info(fd):
    buf = bytearray(ioctl_fs_info_args.size)
    fcntl.ioctl(fd, IOC_FS_INFO, buf)
    return FsInfo(buf)


ioctl_dev_info_args = struct.Struct('=Q16sQQ3032x{0}s'.format(DEVICE_PATH_NAME_MAX))
IOC_DEV_INFO = _IOWR(BTRFS_IOCTL_MAGIC, 30, ioctl_dev_info_args)


class DevInfo(object):
    def __init__(self, buf):
        self.devid, uuid_bytes, self.bytes_used, self.total_bytes, path_bytes = \
            ioctl_dev_info_args.unpack(buf)
        self.path = path_bytes.decode()
        self.uuid = uuid.UUID(bytes=uuid_bytes)

    def __str__(self):
        return "devid {0} uuid {1} bytes_used {2} total_bytes {3} path {4}".format(
            self.devid, self.uuid, self.bytes_used, self.total_bytes, self.path)


def dev_info(fd, devid):
    buf = bytearray(ioctl_dev_info_args.size)
    ioctl_dev_info_args.pack_into(buf, 0, devid, b'', 0, 0, b'')
    fcntl.ioctl(fd, IOC_DEV_INFO, buf)
    return DevInfo(buf)


ioctl_get_dev_stats = struct.Struct('=QQQ5Q968x')
IOC_GET_DEV_STATS = _IOWR(BTRFS_IOCTL_MAGIC, 52, ioctl_get_dev_stats)


class DevStats(object):
    def __init__(self, buf):
        self.devid, self.nr_items, self.flags, self.write_errs, self.read_errs, \
            self.flush_errs, self.generation_errs, self.corruption_errs = \
            ioctl_get_dev_stats.unpack_from(buf)

    @property
    def counters(self):
        return {
            'write': self.write_errs,
            'read': self.read_errs,
            'flush': self.flush_errs,
            'generation': self.generation_errs,
            'corruption': self.corruption_errs,
        }

    def __str__(self):
        return "devid {0} write_errs {1} read_errs {2} flush_errs {3} generation_errs {4} " \
            "corruption_errs {5}".format(self.devid, self.write_errs, self.read_errs,
                                         self.flush_errs, self.generation_errs,
                                         self.corruption_errs)


def dev_stats(fd, devid, reset=False):
    buf = bytearray(ioctl_get_dev_stats.size)
    ioctl_get_dev_stats.pack_into(buf, 0, devid, 5, int(reset), 0, 0, 0, 0, 0)
    fcntl.ioctl(fd, IOC_GET_DEV_STATS, buf)
    return DevStats(buf)


ioctl_space_args = struct.Struct('=2Q')
ioctl_space_info = struct.Struct('=3Q')
IOC_SPACE_INFO = _IOWR(BTRFS_IOCTL_MAGIC, 20, ioctl_space_args)
SpaceArgs = namedtuple('SpaceArgs', ['space_slots', 'total_spaces'])


class SpaceInfo(object):
    def __init__(self, buf, pos):
        self.flags, self.total_bytes, self.used_bytes = ioctl_space_info.unpack_from(buf, pos)
        self.type = self.flags & (BLOCK_GROUP_TYPE_MASK | SPACE_INFO_GLOBAL_RSV)
        self.profile = self.flags & BLOCK_GROUP_PROFILE_MASK
        self.ratio = btrfs.utils.block_group_profile_ratio(self.profile)
        self.raw_total_bytes = self.total_bytes * self.ratio
        self.raw_used_bytes = self.used_bytes * self.ratio

    def __str__(self):
        return "{0}, {1}: total={2}, used={3}".format(
            btrfs.utils.block_group_type_str(self.flags),
            btrfs.utils.block_group_profile_str(self.flags),
            btrfs.utils.pretty_size(self.total_bytes),
            btrfs.utils.pretty_size(self.used_bytes))


def space_args(fd):
    buf = bytearray(ioctl_space_args.size)
    fcntl.ioctl(fd, IOC_SPACE_INFO, buf)
    return SpaceArgs(*ioctl_space_args.unpack(buf))


def space_info(fd):
    args = space_args(fd)
    buf_size = ioctl_space_args.size + ioctl_space_info.size * args.total_spaces
    buf = bytearray(buf_size)
    ioctl_space_args.pack_into(buf, 0, args.total_spaces, 0)
    fcntl.ioctl(fd, IOC_SPACE_INFO, buf)
    return [SpaceInfo(buf, pos)
            for pos in range(ioctl_space_args.size, buf_size, ioctl_space_info.size)]


ioctl_search_key = struct.Struct('=Q6QLLL4x32x')
ioctl_search_args = struct.Struct('{0}{1}x'.format(
    ioctl_search_key.format.decode(), 4096 - ioctl_search_key.size))
ioctl_search_header = struct.Struct('=3Q2L')
IOC_TREE_SEARCH = _IOWR(BTRFS_IOCTL_MAGIC, 17, ioctl_search_args)
SearchHeader = namedtuple('SearchHeader', ['transid', 'objectid', 'offset', 'type', 'len'])


def search(fd, tree, min_key=None, max_key=None,
           min_transid=0, max_transid=ULLONG_MAX,
           nr_items=ULONG_MAX):
    return search_v2(fd, tree, min_key, max_key, min_transid, max_transid,
                     nr_items, _v2=False)


_ioctl_search_args_v2 = [
    ioctl_search_key,
    struct.Struct('=Q')
]
ioctl_search_args_v2 = struct.Struct('=' + ''.join([s.format[1:].decode()
                                                    for s in _ioctl_search_args_v2]))
IOC_TREE_SEARCH_V2 = _IOWR(BTRFS_IOCTL_MAGIC, 17, ioctl_search_args_v2)


def search_v2(fd, tree, min_key=None, max_key=None,
              min_transid=0, max_transid=ULLONG_MAX,
              nr_items=ULONG_MAX, buf_size=None, _v2=True):
    if min_key is None:
        min_key = btrfs.ctree.Key(0, 0, 0)
    if max_key is None:
        max_key = btrfs.ctree.Key(ULLONG_MAX, 255, ULLONG_MAX)
    wanted_nr_items = nr_items
    result_nr_items = -1
    if _v2 and buf_size is None:
        buf_size = 16384
    while min_key <= max_key and result_nr_items != 0 and wanted_nr_items > 0:
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
                yield((header, buf_view[pos:pos+header.len]))
                pos += header.len
                wanted_nr_items -= 1
                if wanted_nr_items == 0:
                    break
            min_key = btrfs.ctree.Key(header.objectid, header.type, header.offset)
            min_key += 1


data_container = struct.Struct('=LLLL')
ioctl_logical_ino_args = struct.Struct('=QQ32xQ')
IOC_LOGICAL_INO = _IOWR(BTRFS_IOCTL_MAGIC, 36, ioctl_logical_ino_args)
inum_offset_root = struct.Struct('=QQQ')
Inode = namedtuple('Inode', ['inum', 'offset', 'root'])


def logical_to_ino(fd, vaddr, bufsize=4096):
    bufsize = min(bufsize, 65536)
    inodes_buf = array.array(u'B', bytearray(bufsize))
    inodes_ptr = inodes_buf.buffer_info()[0]
    args = bytearray(ioctl_logical_ino_args.size)
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
InoLookupResult = namedtuple('InoLookupResult', ['treeid', 'name_bytes'])


def ino_lookup(fd, treeid=0, objectid=FIRST_FREE_OBJECTID):
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


#
# Note: does not implement single usage and limit values, so incompatible with
# kernel < 4.4
#
class BalanceArgs(object):
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

    def for_struct(self):
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

    @property
    def flags_str(self):
        return btrfs.utils.flags_str(self.flags, _balance_args_flags_str_map)

    def __str__(self):
        opts = []
        if self.flags & BALANCE_ARGS_PROFILES:
            opts.append("profiles={}".format(
                btrfs.utils.flags_str(self.profiles, btrfs.ctree._balance_args_profiles_str_map)))
        if self.flags & BALANCE_ARGS_USAGE_RANGE:
            opts.append("usage={}..{}".format(self.usage_min, self.usage_max))
        if self.flags & BALANCE_ARGS_DEVID:
            opts.append("devid={}".format(self.devid))
        if self.flags & BALANCE_ARGS_DRANGE:
            opts.append("drange={}..{}".format(self.pstart, self.pend))
        if self.flags & BALANCE_ARGS_VRANGE:
            opts.append("vrange={}..{}".format(self.vstart, self.vend))
        if self.flags & BALANCE_ARGS_CONVERT:
            opts.append("target={}".format(
                btrfs.utils.flags_str(self.target, btrfs.ctree._balance_args_profiles_str_map)))
        if self.flags & BALANCE_ARGS_LIMIT_RANGE:
            opts.append("limit={}..{}".format(self.limit_min, self.limit_max))
        if self.flags & BALANCE_ARGS_STRIPES_RANGE:
            opts.append("stripes={}..{}".format(self.stripes_min, self.stripes_max))
        if self.flags & BALANCE_ARGS_SOFT:
            opts.append("soft")
        return "flags({}) {}".format(self.flags_str, ', '.join(opts))


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

_balance_args = struct.Struct('=QLL7Q4L48x')
_balance_progress = struct.Struct('=3Q')


class BalanceProgress(object):
    def __init__(self, state, expected, considered, completed):
        self.state = state
        self.expected = expected
        self.considered = considered
        self.completed = completed

    @property
    def state_str(self):
        return btrfs.utils.flags_str(self.state, _balance_state_str_map)

    def __repr__(self):
        return "BalanceProgress(state={self.state:#x}, expected={self.expected}, " \
            "considered={self.considered}, completed={self.completed}".format(self=self)

    def __str__(self):
        return "state {self.state_str} expected {self.expected} considered {self.considered} " \
            "completed {self.completed}".format(self=self)


_ioctl_balance_args = [
    struct.Struct('=Q'),  # 0 - flags - in/out
    struct.Struct('=Q'),  # 1 - state - out
    _balance_args,  # 2 - data - in/out
    _balance_args,  # 3 - meta - in/out
    _balance_args,  # 4 - sys - in/out
    _balance_progress,  # 5 - stat - out
    struct.Struct('=576x')
]
ioctl_balance_args = struct.Struct('=' + ''.join([s.format[1:].decode()
                                                  for s in _ioctl_balance_args]))
IOC_BALANCE_V2 = _IOWR(BTRFS_IOCTL_MAGIC, 32, ioctl_balance_args)


class BalanceError(Exception):
    def __init__(self, state, msg):
        self.state = state
        self.msg = msg

    @property
    def errno(self):
        return self.__context__.errno

    def __str__(self):
        return self.msg


def balance_v2(fd, data_args=None, meta_args=None, sys_args=None, force=False, resume=False):
    args = bytearray(ioctl_balance_args.size)
    if resume:
        _ioctl_balance_args[0].pack_into(args, 0, BALANCE_RESUME)
    else:
        flags = 0
        pos = _ioctl_balance_args[0].size
        pos += _ioctl_balance_args[1].size
        if data_args is not None:
            flags |= BALANCE_DATA
            _balance_args.pack_into(args, pos, *data_args.for_struct())
        pos += _balance_args.size
        if meta_args is not None:
            flags |= BALANCE_METADATA
            _balance_args.pack_into(args, pos, *meta_args.for_struct())
        pos += _balance_args.size
        if sys_args is not None:
            flags |= BALANCE_SYSTEM
            _balance_args.pack_into(args, pos, *sys_args.for_struct())
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
                "state {}".format(errorcode,
                                  btrfs.utils.flags_str(state, _balance_state_str_map))
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
