python-btrfs
============

Python 3 module to inspect btrfs filesystems.

License: LGPL-3.0

Btrfs is a copy on write (COW) filesystem for Linux aimed at implementing
advanced features while focusing on fault tolerance, repair and easy
administration.

Project Goal
------------

The primary goal of this module is to be able to inspect the internals of a
mounted, online, filesystem for educational purposes.

A second goal is to provide a nicer way for automating administration tasks and
writing monitoring scripts by being able to just programmatically access the
needed information, instead of having to spend most of the time on parsing
human readable output from other btrfs tools.

The python module acts as a wrapper around the low level kernel calls and btrfs
data structures, presenting them as python objects with interesting attributes
and references to other objects.

Documentation
-------------

Reference documentation of the stable API of the library is written in Sphinx
autodoc format. An [online version of the HTML
documentation](https://python-btrfs.readthedocs.io/en/stable/btrfs.html) is also
available.
