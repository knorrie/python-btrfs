python-btrfs
============

Python module to inspect btrfs filesystems.

License: GPLv2.

Btrfs is a copy on write (COW) filesystem for Linux aimed at implementing
advanced features while focusing on fault tolerance, repair and easy
administration.

Project Goal
------------

Currently, the primary goal of this module is  to be able to inspect the
internals of an existing filesystem for educational purposes.

The python module acts as a wrapper around the low level kernel calls and btrfs
data structures, presenting them as python objects with interesting attributes
and references to other objects.

Using these helpers, it should be fairly easy to reimplement the same
functionality as for example `btrfs fi df`, `btrfs fi show` and `btrfs
inspect-internal` provide.

Development
-----------

The module is in very early development, support for filesystem structures will
be added one after another.
