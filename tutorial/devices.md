Previous: [Introduction](intro.md)

Devices
=======

Let's have another look at the `btrfs fi show` output that we've seen in the
previous page:

```
-# btrfs fi show
Label: none  uuid: d9aa0273-023c-4d9e-8d93-a575140be799
    Total devices 3 FS bytes used 112.00KiB
    devid    1 size 6.00GiB used 1.60GiB path /dev/loop0
    devid    2 size 6.00GiB used 622.38MiB path /dev/loop1
    devid    3 size 6.00GiB used 1.61GiB path /dev/loop2
```

If you're not familiar with the output of `btrfs fi show` yet:
 * We see that a filesystem exists with filesystem id
   `d9aa0273-023c-4d9e-8d93-a575140be799`
 * The filesystem has 3 block devices attached from which it can allocate space
   to use.
 * For every device, we can see how much raw space is _allocated_ (claimed to
   be used for a particular purpose).  For our new filesystem, this is
   `1.60GiB`, `622.38MiB` and `1.61GiB`, which is `3.81GiB` in total!  While
   this may seem a scary amount for an empty filesystem, we can also see that
   inside that `3.81GiB`, there's luckily actually only `112.00KiB` in use.

python-btrfs and Device Info
----------------------------

Let's look up some more of the same information that `btrfs fi show` showed us.

```
-# python3
>>> import btrfs
>>> fs = btrfs.FileSystem('/mnt/tutorial')
>>> info = fs.dev_info(1)
>>>
>>> btrfs.utils.pretty_print(info)
<btrfs.ioctl.DevInfo>
total_bytes: 6442450944
devid: 1
uuid: d71b5e3f-32b2-4a9b-83f4-d22d8fdfc36d
path: /dev/loop0
bytes_used: 1717960704
>>>

```

Just like `fs_info`, `dev_info` is a function in the kernel code we can
execute. In the background, our `FileSystem` calls this function and asks the
kernel for information about device 1 in this filesystem.

```
>>> btrfs.utils.pretty_size(info.total_bytes)
'6.00GiB'
>>> btrfs.utils.pretty_size(info.bytes_used)
'1.60GiB'
```

Well, that looks familiar!

There's one very annoying thing though... From the `fs_info`, we know that
there are `X` devices and the highest device number is `Y`. However, we need to
call `dev_info` by id. The list of ids does not have to be contiguous, there
can be gaps after removing a device for example. So, it would be more
convenient if we could just look up a list of all devices with their
information...

Directly looking up metadata objects
------------------------------------

The two examples we've seen to far, `fs_info` and `dev_info` are functions that
exist in the kernel. However, the btrfs kernel code does not implement
thousands of functions for every little detail about the filesystem that we
would like to look up. Instead, it provides a generic `search` function, that
can be used to retrieve any metadata object.

Until we do a deeper dive into how metadata trees are organized, and how we can
manually search for objects, we just keep using the convenience functions in
the `Filesystem` class which look up specific metadata for us.

Let's use the `devices()` function to look up metadata about our devices:

```
-# python3
>>> import btrfs
>>> fs = btrfs.FileSystem('/mnt/tutorial')
>>> fs.devices()
<generator object FileSystem.devices at 0x7f08b1d382b0>
```

The function returns... a "generator". If you don't know about generators in
python, then think of them as an iterator though a list whose length is not
known in advance, and whose items are generated on demand, as soon as you ask
for them.  Python-btrfs uses generators in various places, since it allows us
to process large amounts of metadata in a streaming way.

In this case, we know that we only have a few devices, so we'll never run out
of memory if we load all of the objects into an actual list at once.

Let's just load the items into a real list, so we can address each of them
by number:

```
>>> devices = list(fs.devices())
>>> len(devices)
3
```

As expected, we have 3 devices. The three python objects in our list are
objects of the type `btrfs.ctree.DevItem`, which contains fields with the exact
same names as the `btrfs_dev_item` struct in the C code of the linux kernel.

Using the `btrfs.utils.pretty_print` function again, we can show the contents
of this btrfs metadata object:

```
>>> btrfs.utils.pretty_print(devices[0])
<btrfs.ctree.DevItem (DEV_ITEMS DEV_ITEM 1)>
sector_size: 4096
bandwidth: 0
devid: 1
total_bytes: 6442450944
generation: 0
start_offset: 0
bytes_used: 1717960704
type: 0
dev_group: 0
seek_speed: 0
io_width: 4096
fsid: d9aa0273-023c-4d9e-8d93-a575140be799
uuid: d71b5e3f-32b2-4a9b-83f4-d22d8fdfc36d
io_align: 4096
```

As expected, the first device object has the number `1` for `devid`, and we can
also recognize the values for `total_bytes` and `bytes_used` from the `btrfs fi
show` output.

Looking at the `bytes_used` of the other two devices confirms our suspicions:

```
>>> btrfs.utils.pretty_size(devices[0].bytes_used)
'1.60GiB'
>>> btrfs.utils.pretty_size(devices[1].bytes_used)
'622.38MiB'
>>> btrfs.utils.pretty_size(devices[2].bytes_used)
'1.61GiB'
>>> devi2
```

The device metadata object contains a number of interesting looking fields,
like `bandwidth` and `seek_speed`. However, these were added a long time ago in
a non 'design for today' way, and are not used at all.

The careful reader will notice that a field `path` is missing in the actual
metadata objects. This is correct, since the path is dynamically determined by
the `dev_info` function. It is not part of the metadata itself. This might well
be the reason that the `dev_info` function was added.

Device statistics
-----------------

The last function we're going to have a look at is retrieving device statistics.

```
>>> stats = fs.dev_stats(1)
>>> btrfs.utils.pretty_print(stats)
<btrfs.ioctl.DevStats>
corruption_errs: 0
devid: 1
read_errs: 0
nr_items: 5
flags: 0
generation_errs: 0
flush_errs: 0
write_errs: 0
```

Yup, those are the same counters that are printed by `btrfs device stats
/mnt/tutorial`, which also adds the path information that can be found using
`dev_info`. In the kernel code this is the struct named
`btrfs_ioctl_get_dev_stats`.

So, by now we already have seen a few fun simple functions, which we could for
example use to build a monitoring plugin that keeps an eye on device errors,
without having to parse the text output of `btrfs device stats`.

Questions and Exercises
-----------------------

1. Using python-btrfs, write an example program, `btrfs-fi-show.py` that
   provides the same output as `btrfs fi show /<mountpoint>` does, using
   information you can retrieve by calling the `fs_info` and, `dev_info` ioctl
   calls combined with the information from the device objects you can look up
   by calling `devices()` on your `FileSystem` object.

2. Look up the source code of the `btrfs fi show` command from btrfs-progs, and
   try to find out in what way it retrieves the information. Spoiler: it's a
   bit different.

Next: [Space Info](space_info.md)  
Up: [Overview](README.md)
