Previous: [Devices](devices.md)

Space Info
==========

You probably know the `btrfs fi df` command:

```
-# btrfs fi df /mnt/tutorial
Data, RAID0: total=1.80GiB, used=704.00KiB
System, RAID1: total=8.00MiB, used=16.00KiB
Metadata, RAID1: total=1.00GiB, used=112.00KiB
GlobalReserve, single: total=16.00MiB, used=0.00B
```

Each of the lines of the output represents a 'space'. In btrfs terminology, a
'space' is the collection of all disk storage that has the same type and
profile. A 'type' can be data, metadata or system, and a profile is single or
one of the chunk-based raid levels.

As you might guess after reading the previous pages, there's a kernel function
which will provide us with all the data we need, and unsurprisingly, it's
called `space_info`.

```
-# python3
>>> import btrfs
>>> fs = btrfs.FileSystem('/mnt/tutorial')
>>> for space_info in fs.space_info():
...     print(space_info)
...
Data, RAID0: total=1.80GiB, used=704.00KiB
System, RAID1: total=8.00MiB, used=16.00KiB
Metadata, RAID1: total=1.00GiB, used=112.00KiB
GlobalReserve, single: total=16.00MiB, used=0.00B
```

Whelp, that's convenient! The `__str__` function of these objects returns a
string in the same formatting as `btrfs fi df` does.

To quickly see what's actually inside the `space_info` objects, we use our
`pretty_print` function:

```
>>> info = fs.space_info()
>>> btrfs.utils.pretty_print(info)
-
  <btrfs.ioctl.SpaceInfo>
  flags: Data, RAID0
  total_bytes: 1.80GiB
  used_bytes: 704.00KiB
-
  <btrfs.ioctl.SpaceInfo>
  flags: System, RAID1
  total_bytes: 8.00MiB
  used_bytes: 16.00KiB
-
  <btrfs.ioctl.SpaceInfo>
  flags: Metadata, RAID1
  total_bytes: 1.00GiB
  used_bytes: 112.00KiB
-
  <btrfs.ioctl.SpaceInfo>
  flags: GlobalReserve, single
  total_bytes: 16.00MiB
  used_bytes: 0
```

Since the shown field names are just attributes, we can access them easily:

```
>>> info[0].total_bytes
1932656640
>>> btrfs.utils.pretty_size(info[0].total_bytes)
'1.80GiB'
```

Etc...

Types and Profiles
------------------

In the space info data, we see that btrfs has data and metadata, and for each
of them there can be a profile chosen, like single, RAID0 or RAID1. It's even
possible to have multiple space info objects for data or metadata. Typically,
it's not recommended to have mixed profiles in the filesystem for a single
type, but while doing a conversion between profile types, we obviously would
see them both here.

In the next page of the tutorial, we meet the chunks, which are a very
important basic building block of btrfs. Chunks are pieces of raw disk space
that are claimed for use for a specific space.

Next: [Chunks](chunks.md)  
Up: [Overview](README.md)
