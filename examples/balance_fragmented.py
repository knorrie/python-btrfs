#!/usr/bin/python3

import btrfs
import heatmap
import math
import os
import shutil
import sys
import time

if len(sys.argv) < 3:
    print("Usage: {} <min_score> <mountpoint>".format(sys.argv[0]))
    sys.exit(1)

min_score = int(sys.argv[1])
os.makedirs('heatmap', exist_ok=True)

skipped_max_usage = skipped_min_fragmented = skipped_gone = 0


with btrfs.FileSystem(sys.argv[2]) as fs:
    for chunk in fs.chunks():
        if chunk.type != btrfs.BLOCK_GROUP_DATA:
            continue
        try:
            block_group = fs.block_group(chunk.vaddr, chunk.length)
        except IndexError:
            skipped_gone += 1
            continue
        if block_group.used_pct >= 90:
            skipped_max_usage += 1
            continue

        min_vaddr = block_group.vaddr
        max_vaddr = block_group.vaddr + block_group.length - 1

        log2_bg_length = math.log2(block_group.length)
        half_width = (log2_bg_length - 11) / 2
        shift = (log2_bg_length + 11) / 2

        score = 0
        if block_group.used != block_group.length:
            for free_space_extent in fs.free_space_extents(min_vaddr, max_vaddr):
                bad = 1 - abs((math.log2(free_space_extent.length) - shift) / half_width)
                score += bad
        if score >= min_score:
            print("skipped max_usage {} min_fragmented {} gone {}".format(
                skipped_max_usage, skipped_min_fragmented, skipped_gone), flush=True)

            grid = heatmap.walk_extents(fs, [block_group], size=9, verbose=-1)
            png_filename = "heatmap/{}-{:06d}-{}-{}.png".format(
                int(time.time()), int(score), block_group.used_pct, block_group.vaddr)
            print(png_filename, flush=True)
            grid.write_png(png_filename)
            shutil.copy2(png_filename, 'heatmap/now.png')
            args = btrfs.ioctl.BalanceArgs(vstart=min_vaddr, vend=min_vaddr+1)
            try:
                print(btrfs.ioctl.balance_v2(fs.fd, data_args=args), flush=True)
            except Exception as e:
                print(e)
                sys.exit(0)
        else:
            skipped_min_fragmented += 1
