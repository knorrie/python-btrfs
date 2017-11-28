#!/usr/bin/python3

import btrfs
import math
import sys

if len(sys.argv) < 2:
    print("Usage: {} [min_score] <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

fs = btrfs.FileSystem(sys.argv[-1])
if len(sys.argv) == 3:
    min_score = int(sys.argv[1])
else:
    min_score = 250
print("Showing all block groups with free space fragmentation score >= {}".format(min_score))


def extent_tree_free_space_extents(min_vaddr, max_vaddr):
    cur_end = min_vaddr
    for extent in fs.extents(min_vaddr, max_vaddr):
        next_start = extent.vaddr
        if isinstance(extent, btrfs.ctree.ExtentItem):
            next_end = next_start + extent.length
        elif isinstance(extent, btrfs.ctree.MetaDataItem):
            next_end = next_start + fs.nodesize
        if next_start > cur_end:
            yield btrfs.free_space_tree.FreeSpaceExtent(cur_end, next_start - cur_end)
        cur_end = next_end
    if cur_end < max_vaddr:
        yield btrfs.free_space_tree.FreeSpaceExtent(cur_end, max_vaddr + 1 - cur_end)


try:
    list(fs.free_space_extents(0, 0))
    free_space_extents = fs.free_space_extents
except:
    print("No Free Space Tree (space_cache=v2) found!")
    print("Falling back to using the extent tree to determine free space extents.")
    free_space_extents = extent_tree_free_space_extents

bad_chunks = 0
for chunk in fs.chunks():
    if not chunk.type & btrfs.BLOCK_GROUP_DATA:
        continue
    try:
        block_group = fs.block_group(chunk.vaddr, chunk.length)
    except IndexError:
        continue

    min_vaddr = block_group.vaddr
    max_vaddr = block_group.vaddr + block_group.length - 1

    log2_bg_length = math.log2(block_group.length)
    half_width = (log2_bg_length - 11) / 2
    shift = (log2_bg_length + 11) / 2
    # When drawing the function seen below (score += ...), like...
    #
    #         | x - shift  |
    # y = 1 - | ---------- |
    #         | half_width |
    #
    # ... you'll see an upside down V shape. The x values are the log2() of a
    # free space extent size, so e.g. 16 for 64KiB of free space. The y value
    # is the fragmentation score. The function will give a low score to free
    # space fragments that are very small (but when you have an enormous amount
    # of them, it'll add up again) and also a low score to very big ones
    # (they're good). Fragments in the middle get a higher score.
    #
    # Experience learns that scores above 250 point at chunks in which free
    # space fragmentation is getting quite bad. Use btrfs-heatmap to create
    # images of specific block groups to see what's happening inside.
    fragments = 0
    score = 0
    for free_space_extent in free_space_extents(min_vaddr, max_vaddr):
        fragments += 1
        score += 1 - abs((math.log2(free_space_extent.length) - shift) / half_width)
    if score >= min_score:
        bad_chunks += 1
        print("vaddr {} length {} used_pct {} free space fragments {} score {}".format(
            chunk.vaddr, chunk.length, block_group.used_pct, fragments, int(score)))

if bad_chunks == 0:
    print("No block groups found with free space fragmentation score >= {}".format(min_score))
