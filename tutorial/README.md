A Btrfs Tutorial
================

You have heard about this new filesystem, called btrfs, and started using it.
After a while you either ran into problems or started to become curious about
the inner workings of this filesystem.

Where does this filesystem actually put data on my disk? How are these things
called subvolumes able to snapshot themselves so quickly and able to provide a
view on a previous version of my data while I can keep making changes? How are
`cp --reflink` and deduplication related? How can I find out what `btrfs
balance` actually is doing, and why I need to run it or not?

You join the `#btrfs` IRC channel and see people making jokes about cows and
trees all the time...

In this tutorial, I'll take you on a journey through the structure of a btrfs
filesystem. Using the python-btrfs library, we will explore how the metadata of
a btrfs filesystem is organized, and how exposed functions in the btrfs kernel
API (the IOCTL calls) can be used.

Some of the parts of the tutorial have questions and exercises. The answers to
them are not included. If you want to discuss your answers to the questions, or
want to show python code fragments written to solve the exercises, then don't
hesitate to talk to me on IRC (Knorrie) or drop me an email at
`hans@knorrie.org`.

_N.B. the python-btrfs library deals with mounted (on-line) btrfs file systems
only. Whenever data or metadata gets damaged and the filesystem cannot be
mounted any more, then none of its functionality can help us solve that._

Part I - Exploring the filesystem structure
--------------------------------------------

In this part we will discover how btrfs keeps an administration of disk space
usage and how we can find out where all of our data is placed on disk. Instead
of diving into technical details about how btrfs metadata is organized
internally, we just use convenience functions in the python-btrfs library.

 * [Creating a test file system, introduction to python-btrfs](intro.md)
 * [Device information and looking up metadata](devices.md)
 * [Space Info](space_info.md)
 * [Chunks and the physical and virtual address space](chunks.md)
 * [Block Groups and Extents](block_groups.md)

Part II - Trees and Cows
------------------------

 * [Trees](trees.md)
 * [Cows](cows.md)

Part III - Climbing the trees, Moo!
-----------------------------------

Now that we have a bit of an idea about some types of metadata that is stored
about the filesystem, we stop using the helpers in the FileSystem object and
have a look at trees directly.

 * [Tree keys and the tree search ioctl](keys.md)
 * [The filesystem tree](fs_tree.md)
 * [The free space tree](free_space_tree.md)

Part IV - Advanced btrfs features
---------------------------------------

 * [Subvolumes, snapshots and reflinks](subvolumes.md)
 * [Extent backreferences and the logical to inode to path name ioctls](logical_to_ino_lookup.md)
 * [Balance](balance.md)
 * [Deduplication](dedupe.md)
