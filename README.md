python-btrfs
============

## What is python-btrfs?

python-btrfs is a Python 3 library that provides ways to interact
programmatically with an online btrfs file system.

It provides a pure python shadow implementation of data structures used in
btrfs together with convenient wrappers around the collection of kernel
functions that are available in the btrfs kernel API.

Using them, we can examine the secret inner world of a btrfs file system for
educational purposes.

## Where do I get it?

Your favourite GNU/Linux distro probably has it packaged as either python-btrfs
or python3-btrfs package.

This git repository with source code can also directly be used with python 3.
No dependencies other than the python standard library are needed.

## Should I be using this?

The target audience for using the library is system administrators and
developers who want to discover more about the internals of a btrfs file
system, or want to create adjusted monitoring or administration tools that are
optimized for their specific use cases.

Of course, it's python, so, this is for who prefers programming python over
programming C for quickly building fun stuff.

## I have a broken file system, can I repair it using python-btrfs?

python-btrfs does not directly access disk storage, it only uses functions
available in the kernel interface, using system calls. This also means that
python-btrfs can not be used to repair a broken filesystem whenever the running
Linux kernel cannot properly mount it.

## What can I do with python-btrfs?

Using it allows one to take a peek behind the curtains of the regular
functionality provided by the
[btrfs-progs](https://github.com/kdave/btrfs-progs/blob/master/README.md)
programs and the
[libbtrfsutil](https://github.com/kdave/btrfs-progs/blob/master/libbtrfsutil/README.md)
C and Python library.

You can basically do anything that btrfs-progs or libbtrfsutil can do with an
online file system.  However, at the same time we're operating on a bit lower
abstraction level. However again, that allows us to also be creative and make
optimized utilities for our own special use cases.

An example is the `btrfs-balance-least-used` program that you can find in the
`bin` directory. It's a modified algorithm for using btrfs balance to compact
allocated space (i.e. defragment free space) as fast and efficient as possible
by taking the usage ratio of the individual allocations of raw disk space into
account.

## Show me some example code!

Let's for example have a look at the equivalent of the `btrfs fi df /` command:

```python3
>>> import btrfs
>>> with btrfs.FileSystem('/') as fs:
...     for space in fs.space_info():
...         print(space)
... 
Data, single: total=839.01GiB, used=838.47GiB
System, DUP: total=8.00MiB, used=112.00KiB
Metadata, DUP: total=4.00GiB, used=2.38GiB
GlobalReserve, single: total=512.00MiB, used=0.00B
```

Well, that was easy! But, say, instead of this text, you want to create a pie
chart out of it. Now, instead of writing a horrible program that parses back
the text output of the `btrfs fi df` command, we can access the values
directly.

```python3
>>> spaces = fs.space_info()
>>> len(spaces)
4
```

The `space_info()` function calls the `SPACE_INFO` kernel function, which returns
a list of `SpaceInfo` objects. By feeding one of those to the pretty printer in
the utils module, we can see all contents. The attributes are directly
accessible in our code:

```python3
>>> btrfs.utils.pretty_print(spaces[0])
<btrfs.ioctl.SpaceInfo>
flags: Data, single
total_bytes: 839.01GiB
used_bytes: 838.50GiB

>>> spaces[0].flags
1
>>> btrfs.utils.block_group_flags_str(spaces[0].flags)
'DATA'
>>> spaces[0].total_bytes
900877778944
```

So, using these values, we could create a nice picture using an imaging library.

## More examples!

The `bin` and `examples` directory in the source code contain an example
collection of programs that are built using the library.

## Documentation

Reference documentation of the stable API of the library is written in Sphinx
autodoc format. An [online version of the HTML
documentation](https://python-btrfs.readthedocs.io/en/stable/genindex.html) is also
available.

In general, the
[`btrfs.FileSystem`](https://python-btrfs.readthedocs.io/en/stable/btrfs.html#btrfs.ctree.FileSystem)
object, shown above, is the best starting point for exploring available
functionality.

Tutorial style documentation will be added in the future.

## License

The python-btrfs library itself is licensed under the LGPL-3.0.

Example scripts in the bin directory are licensed under the MIT License
(Expat). Feel free to use all the ideas and code from them to build new stuff using python-btrfs!
