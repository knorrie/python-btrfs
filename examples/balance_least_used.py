#!/usr/bin/python3

import btrfs
import heapq
import sys
import time


def load_block_groups(fs, max_used_pct):
    min_used_pct = 101
    block_groups = []
    print("Loading block group objects with used_pct <= {} ...".format(max_used_pct),
          end='', flush=True)
    for chunk in fs.chunks():
        if not (chunk.type & btrfs.BLOCK_GROUP_DATA):
            continue
        try:
            block_group = fs.block_group(chunk.vaddr, chunk.length)
            if block_group.used_pct <= max_used_pct:
                block_groups.append((block_group.used_pct, block_group))
            if block_group.used_pct < min_used_pct:
                min_used_pct = block_group.used_pct
        except IndexError:
            continue
    heapq.heapify(block_groups)
    print(" found {}".format(len(block_groups)))
    return min_used_pct, block_groups


def balance_one_block_group(fs, block_groups, max_used_pct):
    next_used_pct, next_block_group = block_groups[0]
    try:
        block_group = fs.block_group(next_block_group.vaddr, next_block_group.length)
    except IndexError:
        heapq.heappop(block_groups)
        return
    vaddr = block_group.vaddr
    used_pct = block_group.used_pct
    if used_pct > next_used_pct:
        if used_pct > max_used_pct:
            print("Ignoring block group vaddr {} used_pct changed {} -> {}".format(
                vaddr, next_used_pct, used_pct))
            heapq.heappop(block_groups)
        else:
            print("Postponing block group vaddr {} used_pct changed {} -> {}".format(
                vaddr, next_used_pct, used_pct))
            heapq.heapreplace(block_groups, (used_pct, block_group))
        return

    start_time = time.time()
    heapq.heappop(block_groups)
    args = btrfs.ioctl.BalanceArgs(vstart=vaddr, vend=vaddr+1)
    print("Balance block group vaddr {} used_pct {} ...".format(
        vaddr, used_pct), end='', flush=True)
    try:
        progress = btrfs.ioctl.balance_v2(fs.fd, data_args=args)
        end_time = time.time()
        print(" duration {} sec total {}".format(int(end_time - start_time), progress.considered))
    except KeyboardInterrupt:
        end_time = time.time()
        print(" duration {} sec".format(int(end_time - start_time)))
        raise


def main():
    max_used_pct = int(sys.argv[1])
    fs = btrfs.FileSystem(sys.argv[2])
    min_used_pct, block_groups = load_block_groups(fs, max_used_pct)
    if len(block_groups) == 0:
        print("Nothing to do, least used block group has used_pct {}".format(min_used_pct))
        return
    while len(block_groups) > 0:
        balance_one_block_group(fs, block_groups, max_used_pct)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: {} <max_used_pct> <mountpoint>".format(sys.argv[0]))
        sys.exit(1)

    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(130)  # 128 + SIGINT
    except Exception as e:
        print(e)
        sys.exit(1)
