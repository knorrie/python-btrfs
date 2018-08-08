A test filesystem and the python-btrfs library
==============================================

This page of the tutorial explains how to set up a test file system, and how to
use the python-btrfs library to start showing details about it after we bring
it online.

Creating a test filesystem
--------------------------

Before we can inspect a btrfs filesystem, we need to have one. If you have an
existing btrfs filesystem, then it's perfectly fine to use that for most of the
parts of the tutorial.

However, to have a small example filesystem for this tutorial, I'll create a
small filesystem by combining three disks of 6GiB size. The disks are fake, and
just based on files, which is an easy way to create a test filesystem:

```
-# dd if=/dev/zero of=device1 bs=1 count=0 seek=6G
-# dd if=/dev/zero of=device2 bs=1 count=0 seek=6G
-# dd if=/dev/zero of=device3 bs=1 count=0 seek=6G

-# mkfs.btrfs device1 device2 device3

-# losetup -f device1
-# losetup -f device2
-# losetup -f device3
```

After doing so, `btrfs fi show` detects our new file system:

```
-# btrfs fi show
Label: none  uuid: d9aa0273-023c-4d9e-8d93-a575140be799
    Total devices 3 FS bytes used 112.00KiB
    devid    1 size 6.00GiB used 1.60GiB path /dev/loop0
    devid    2 size 6.00GiB used 622.38MiB path /dev/loop1
    devid    3 size 6.00GiB used 1.61GiB path /dev/loop2
```

python-btrfs and the FileSystem object
--------------------------------------

python-btrfs is a python library that contains a pure python implementation of
the btrfs metadata object types, together with an implementation of the calling
side of various btrfs-related functions that the linux kernel exposes.

Using the library, we can only read metadata information, we cannot directly
change it. Changing metadata happens in the background as a side effect of
using regular linux kernel VFS functionality, i.e. everything you can do like
`cat`, `cp`, `touch`, `mv`, `mkdir`, etc...

The btrfs module has a `FileSystem` object, which provides a number of helper
functions to get us started, without having to know much detail about where
exactly to find metadata objects yet.

But first, we have to mount our test filesystem somewhere:

```
-# mount -o noatime /dev/loop0 /mnt/tutorial
```

Now, let's fire up an interactive python session and use the btrfs library to
look up some information about it.

```
-# python3
>>> import btrfs
>>> fs = btrfs.FileSystem('/mnt/tutorial')
>>> info = fs.fs_info()
>>>
>>> btrfs.utils.pretty_print(info)
<btrfs.ioctl.FsInfo>
max_id: 3
num_devices: 3
nodesize: 16384
fsid: d9aa0273-023c-4d9e-8d93-a575140be799
clone_alignment: 4096
sectorsize: 4096
>>>
>>> info.fsid
UUID('d9aa0273-023c-4d9e-8d93-a575140be799')
```

The above commands import the btrfs library and create a `FileSystem` object
that allows us to look into the filesystem mounted at `/mnt/tutorial`.  Next,
we call the `fs_info()` function, which executes the `fs_info` function that is
exposed in the btrfs linux kernel API, pointing it to this filesystem.

It returns a little object with some fields with information about the
filesystem.  One of the fields is the `fsid`, which we recognize from the
`btrfs fi show` output. It also tells us that we have 3 devices connected to
the filesystem and that the size of metadata blocks on disk is 16 kilobytes,
and a few more things.

python-btrfs, kernel code and naming things
-------------------------------------------

When writing the python-btrfs library, I tried to keep names of functions and
objects as similar as possible to their name in the linux kernel C code, after
translating them to a Pythonesque style.

For example, the `info` object above is of type `btrfs.ioctl.FsInfo`, which
corresponds to the `btrfs_ioctl_fs_info_args` struct in the kernel code.

Next: [Devices](devices.md)  
Up: [Overview](README.md)
