Previous: [Chunks](chunks.md)

Block Groups and Extents
========================

In the previous page, we've seen that the collection of chunks together
determines the virtual address space in a btrfs filesystem. The information
provided by the chunk objects is a mapping to the place where the data is
stored on actual underlying block devices.

The Block Group
---------------

The btrfs block group is an object that is very similar to the chunk. The main
difference is that instead of looking down at the disks, they're looking in the
opposite direction, providing us with more information about the data which is
actually stored inside this allocated piece of virtual address space.

Let's start by looking up our block group objects with python-btrfs:

```
-# python3
>>> import btrfs
>>> fs = btrfs.FileSystem('/mnt/tutorial')
>>> for chunk in fs.chunks():
...     print(fs.block_group(chunk.vaddr))
...
block group vaddr 20971520 length 8388608 flags SYSTEM|RAID1 used 16384 used_pct 0
block group vaddr 29360128 length 1073741824 flags METADATA|RAID1 used 114688 used_pct 0
block group vaddr 1103101952 length 1932656640 flags DATA|RAID0 used 720896 used_pct 0
```

When comparing this with the chunks on the previous page, we can see that
there's a one to one mapping of block group address and length to chunk address
and length. The flags are also exactly the same.

A new field is the `used` field, which shows the amount of bytes that's
actually in use by written data or metadata.

Another thing that the careful reader will notice is that we cannot simply do
`for block_group in fs.block_groups()`, but we're getting the chunk list, and
then looking up the block group objects one by one. Later, when we're going to
look at the metadata search function and trees (and especially the extent tree)
directly, I'll explain why this is.

Extents
-------

A btrfs extent is a single piece of data or metadata that's written. I.e. the
extents store the actual data of files that you write to the filesystem.  The
minimum size of an extent is the `sectorsize` of the filesystem, which can be
found in the `fs_info` object we've seen earlier. Usually, this is 4kiB:

```
>>> fs.fs_info().sectorsize
4096
```

The maximum size of an extent is 128MiB, which is a set of 32768 contiguous
4KiB disk blocks. This 128MiB is a fixed upper limit. When copying files to a
btrfs filesystem, the btrfs kernel module decices for its own how the data of
the file is chopped up in extents. If the file is bigger than 128MiB, it'll
obviously end up being written to more than one extent. Also, btrfs might
decide to split up data from a file a bit to fit sizeable pieces into multiple
pieces of free space that are available.

So, how does this relate to the block groups? Extents and the `sectorsize`
blocks they occupy are grouped together in... Block Groups!

Now, let's have a look at the extents in our little example filesystem. I know
I have a `SYSTEM` type block group at address 20971520 with length 8388608. So,
I can look up all extents in that range, and pretty print them:

```
>>> system_bg = fs.block_group(20971520)
>>> start = system_bg.vaddr
>>> end = system_bg.vaddr + system_bg.length - 1
>>> btrfs.utils.pretty_print(fs.extents(start, end))
-
  <btrfs.ctree.MetaDataItem (20987904 METADATA_ITEM 0)>
  vaddr: 20987904 (key objectid)
  skinny_level: 0 (key offset)
  generation: 5
  flags: TREE_BLOCK
  refs: 1
```

Oh, well, that was disappointing. Only one... Actually, we could have known,
because the total used bytes in this block group is 16384, which can only mean
that there's only one 16kiB metadata extent. In fact, this `SYSTEM` block group
type is a bit special, since it's a special part of the metadata that gets
stored in here, namely the chunk tree. And inside the chunk tree, the chunk
objects we've listed a few times are stored. Apparently all of them fit inside
a single 16kiB metadata page.

Let's spice it up!
------------------

So far things have been rather boring, since we've been looking at an empty
filesystem. I'm going to make my example filesystem a bit more interesting by
copying some data into it.

If you have another existing btrfs filesystem, you can of course also start
inspecting that one instead of doing the same.

Let's copy some data into it now.  An easy way to fill it up with various files
with interesting names and sizes is to just copy the contents of `/usr/` of
another filesystem into it:

```
-# mkdir /mnt/tutorial/usr
-# rsync -av /usr/ /mnt/tutorial/usr/
```

This copies about 4.7GiB of data in my case, which should fit nicely into the
6GiB test filesystem.

Let's have a look at the result:

```
-# python3
>>> import btrfs
>>> fs = btrfs.FileSystem('/mnt/tutorial')
>>> for chunk in fs.chunks():
...     print(fs.block_group(chunk.vaddr))
...
block group vaddr 20971520 length 8388608 flags SYSTEM|RAID1 used 16384 used_pct 0
block group vaddr 29360128 length 1073741824 flags METADATA|RAID1 used 139214848 used_pct 13
block group vaddr 1103101952 length 1932656640 flags DATA|RAID0 used 1932591104 used_pct 100
block group vaddr 3035758592 length 1962934272 flags DATA|RAID0 used 1962934272 used_pct 100
block group vaddr 4998692864 length 1962934272 flags DATA|RAID0 used 943910912 used_pct 48
```

The first `DATA` block group has been filled up, and in the end, two additional
new ones had to be created to make sure extents for all new files could be
written somewhere. When creating these extra block groups, there were also
chunk objects created, and raw disk space was allocated to back them.

Let's list the first 5 extents that are in the block group at `vaddr 4998692864`:

```
>>> start = 4998692864
>>> end = 4998692864 + 1962934272 - 1
>>> extents = fs.extents(start, end)
>>> extents
<generator object FileSystem.extents at 0x7fc8bcb6d360>
```

Yup, extents is a generator now. By calling the extents function we don't
immediately get overwhelmed with extent objects, but we get a generator, which
backs the metadata search query, and which will give us extent objects whenever
we're ready and ask for them.

```
>>> for _ in range(5):
...     btrfs.utils.pretty_print(next(extents))
...     print()
...
<btrfs.ctree.ExtentItem (4998692864 EXTENT_ITEM 3084288)>
vaddr: 4998692864 (key objectid)
length: 3084288 (key offset)
refs: 1
generation: 30
flags: DATA

<btrfs.ctree.ExtentItem (5001777152 EXTENT_ITEM 569344)>
vaddr: 5001777152 (key objectid)
length: 569344 (key offset)
refs: 1
generation: 30
flags: DATA

<btrfs.ctree.ExtentItem (5002346496 EXTENT_ITEM 36864)>
vaddr: 5002346496 (key objectid)
length: 36864 (key offset)
refs: 1
generation: 30
flags: DATA

<btrfs.ctree.ExtentItem (5002383360 EXTENT_ITEM 16384)>
vaddr: 5002383360 (key objectid)
length: 16384 (key offset)
refs: 1
generation: 30
flags: DATA

<btrfs.ctree.ExtentItem (5002399744 EXTENT_ITEM 4096)>
vaddr: 5002399744 (key objectid)
length: 4096 (key offset)
refs: 1
generation: 30
flags: DATA
```

Here we see a bunch of data extents of various sizes. Later on in the tutorial
we'll learn how to find out which extents belong to which actual files we can
see when we do `ls`.

Bonus: Btrfs Heatmap
--------------------

A while ago, I wrote a program called [Btrfs
Heatmap](https://github.com/knorrie/btrfs-heatmap/), which is using the
python-btrfs library to look up information about a filesystem, and which
writes out nice png images to visualize the space usage. The program is a good
example of fun things that can be built on top of python-btrfs, having easy
access to internal information about the filesystem.

### The physical address space

By default, btrfs-heatmap shows a picture of the physical address space, by
just appending the physical space of all connected devices together. In the
following picture, you can clearly see that we have three different disks,
which all are filled for a bit. The bright white space is 100% filled, the gray
space are the Device Extents that contain data for the 48% filled block group,
and the metadata part is only filled for 13%, which is why it's blue, but not
bright blue at all.

The image uses a [Hilbert
Curve](https://github.com/knorrie/btrfs-heatmap/blob/master/doc/curves.md) to
sort things. It nicely keeps all pixels for our Device Extents near each other.

```
-# ./heatmap.py --size 8 -o heatmap-tutorial-physical.png /mnt/tutorial
scope device 1 2 3
grid curve hilbert order 5 size 8 height 32 width 32 total_bytes 19327352832 bytes_per_pixel 18874368.0
pngfile heatmap-tutorial-physical.png
```

| The physical address space, Device Extents |
|:--:|
|![heatmap-tutorial-physical](block_groups/heatmap-tutorial-physical.png)|

btrfs-heatmap can also make pictures where the raw space is sorted on virtual
address space, and detailed pictures about single block groups, to see where
exactly data exents are placed, or where exactly metadata tree blocks are
placed, and what type of three they belong to. Refer to the btrfs-heatmap
documentation for more information.

The next page skips to the second part of the tutorial, an intermezzo in which
we have a look at two of the most important basic concepts of btrfs, Trees and
Cows!

Next: [Trees](trees.md)  
Up: [Overview](README.md)
