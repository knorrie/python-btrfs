#!/usr/bin/python3

import btrfs
import errno
import sys

if len(sys.argv) < 3:
    print("Usage: {} <vaddr> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)


def using_v1(fd, vaddr):
    return btrfs.ioctl.logical_to_ino(fd, vaddr)


def using_v2(fd, vaddr):
    inodes, bytes_missed = btrfs.ioctl.logical_to_ino_v2(fd, vaddr, ignore_offset=True)
    if bytes_missed > 0:
        inodes, bytes_missed = \
            btrfs.ioctl.logical_to_ino_v2(fd, vaddr, bufsize=65536+bytes_missed,
                                          ignore_offset=True)
    return inodes, bytes_missed


def find_out_about_v1_or_v2(fd, vaddr):
    global logical_to_ino_fn
    try:
        inodes, bytes_missed = using_v2(fd, vaddr)
        logical_to_ino_fn = using_v2
        return inodes, bytes_missed
    except IOError as e:
        if e.errno == errno.ENOTTY:
            inodes, bytes_missed = using_v1(fd, vaddr)
            logical_to_ino_fn = using_v1
            return inodes, bytes_missed
        raise


vaddr = int(sys.argv[1])
path_cache = {}

with btrfs.FileSystem(sys.argv[2]) as fs:
    block_group = fs.block_group(vaddr)
    print(block_group)

    logical_to_ino_fn = find_out_about_v1_or_v2

    for extent in fs.extents(vaddr, vaddr + block_group.length - 1):
        if isinstance(extent, btrfs.ctree.ExtentItem) \
                and extent.flags & btrfs.ctree.EXTENT_FLAG_DATA:
            print(extent)
            inodes, bytes_missed = logical_to_ino_fn(fs.fd, extent.vaddr)
            for inode in inodes:
                if inode.root == btrfs.ctree.FS_TREE_OBJECTID or \
                    (inode.root >= btrfs.ctree.FIRST_FREE_OBJECTID and
                     inode.root <= btrfs.ctree.LAST_FREE_OBJECTID):
                    cache_key = (inode.root, inode.inum)
                    if cache_key not in path_cache:
                        try:
                            path = btrfs.ioctl.ino_lookup(fs.fd, treeid=inode.root,
                                                          objectid=inode.inum)[1][:-1]
                            path_cache[cache_key] = btrfs.utils.embedded_text_for_str(path)
                        except IOError as e:
                            if e.errno == errno.ENOENT:
                                path_cache[cache_key] = None
                            else:
                                raise
                    print("    root {} inode {} offset {} path {}".format(
                        inode.root, inode.inum, inode.offset, path_cache[cache_key]))
                else:
                    print("    root {} inode {} offset {}".format(
                        inode.root, inode.inum, inode.offset))
            if len(inodes) == 0 and logical_to_ino_fn == using_v1:
                print("    [... no result and no kernel support for LOGICAL_INO_V2]")
            if bytes_missed > 0:
                if logical_to_ino_fn == using_v1:
                    print("    [... remainder can't be shown; no kernel support for LOGICAL_INO_V2]")  # noqa
                else:
                    print("    [... remainder can't be shown; too many items for buffer size]")
