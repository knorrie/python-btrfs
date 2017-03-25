#!/usr/bin/python3

from btrfs.ctree import (
    ULLONG_MAX, ULONG_MAX,
    Key,
    EXTENT_TREE_OBJECTID, BLOCK_GROUP_ITEM_KEY
)
import btrfs
import random
import sys
import time

if len(sys.argv) < 2:
    print("Usage: {} <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

fs = btrfs.FileSystem(sys.argv[1])
if len(sys.argv) > 2:
    vaddr = int(sys.argv[2])
    chunks = list(fs.chunks(vaddr, vaddr, 1))
    if len(chunks) != 1:
        print("no chunk at vaddr {}".format(vaddr))
        sys.exit(1)
    chunk = chunks[0]
else:
    print("No block group vaddr given, loading chunk tree and selecting a random one.")
    start = time.time()
    chunks = list(fs.chunks())
    now = time.time()
    chunk = chunks[random.randint(0, len(chunks)-1)]
    print("    {:.6f} sec choosing block group at {}".format(now-start, chunk.vaddr))


def time_bg_search(vaddr, length, nr_items):
    tree = EXTENT_TREE_OBJECTID
    min_offset = length if length is not None else 0
    max_offset = length if length is not None else ULLONG_MAX
    min_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, min_offset)
    max_key = Key(vaddr, BLOCK_GROUP_ITEM_KEY, max_offset)
    print("\nmin {}\nmax {}\nnr_items {}".format(min_key, max_key, nr_items))
    start = time.time()
    for header, data in btrfs.ioctl.search_v2(fs.fd, tree, min_key, max_key, nr_items=nr_items):
        bg = btrfs.ctree.BlockGroupItem(header, data)
        now = time.time()
        print("    {:.6f} sec result {}".format(now-start, bg.key))
        start = now
    now = time.time()
    print("    {:.6f} sec done".format(now-start))


time_bg_search(chunk.vaddr, chunk.length, 1)
time_bg_search(chunk.vaddr, None, 1)
time_bg_search(chunk.vaddr, None, 4096)
time_bg_search(chunk.vaddr, chunk.length, ULONG_MAX)
time_bg_search(chunk.vaddr, None, ULONG_MAX)
