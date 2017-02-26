#!/usr/bin/python3

import argparse
import btrfs
import sys


def arg_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-b', '--raw',
        action='store_true',
        help="raw numbers in bytes",
    )
    parser.add_argument(
        '-h', '--human-readable',
        action='store_true',
        help="human friendly numbers, base 1024 (default)",
    )
    parser.add_argument(
        '-H',
        action='store_true', dest='human_si',
        help="human friendly numbers, base 1000",
    )
    parser.add_argument(
        '--iec',
        action='store_true',
        help="use 1024 as a base (KiB, MiB, GiB, TiB)",
    )
    parser.add_argument(
        '--si',
        action='store_true',
        help="use 1000 as a base (kB, MB, GB, TB)",
    )
    parser.add_argument(
        '-k',
        '--kbytes',
        action='store_true',
        help="show sizes in KiB, or kB with --si",
    )
    parser.add_argument(
        '-m',
        '--mbytes',
        action='store_true',
        help="show sizes in MiB, or MB with --si",
    )
    parser.add_argument(
        '-g',
        '--gbytes',
        action='store_true',
        help="show sizes in GiB, or GB with --si",
    )
    parser.add_argument(
        '-t',
        '--tbytes',
        action='store_true',
        help="show sizes in TiB, or TB with --si",
    )
    parser.add_argument(
        'path',
        nargs=1,
    )
    parser.add_argument(
        'junk',
        nargs='*',
        help=argparse.SUPPRESS,
    )
    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()
    unit = None
    binary = True
    if args.raw:
        unit = ''
    if args.human_readable:
        unit = None
    if args.human_si:
        unit = None
        binary = False
    if args.iec:
        binary = True
    if args.si:
        binary = False
    if args.kbytes:
        unit = 'K'
    if args.mbytes:
        unit = 'M'
    if args.gbytes:
        unit = 'G'
    if args.tbytes:
        unit = 'T'
    if len(args.junk) > 0:
        parser.print_help(sys.stderr)
        return

    fs = btrfs.FileSystem(args.path[0])
    for space in fs.space_info():
        print("{}, {}: total={}, used={}".format(
              btrfs.utils.block_group_type_str(space.flags),
              btrfs.utils.block_group_profile_str(space.flags),
              btrfs.utils.pretty_size(space.total_bytes, unit, binary),
              btrfs.utils.pretty_size(space.used_bytes, unit, binary)))


if __name__ == '__main__':
    main()
