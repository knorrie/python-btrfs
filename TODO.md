python-btrfs roadmap
====================

### Intermezzo - btrfs-heatmap

* reimplement heatmap (examples) for the whole filesystem
* "walking" heatmap for block group details (free space fragmentation)

### v0.2 - The Heatmap

* convert the existing nagios plugin to use this lib
* changelog

### v0.3 - More data structures

* finish listing the extent tree: metadata
* based on extents, list files that use them (fs tree, inodes) (with full path)

### v0.4 - Documentation

Target audience: sysadmin with a bit of programming knowledge that does not
want to parse output of btrfs xyz commands with regexes.

* Getting started!
* What's in the source code?
* Some more examples explained

### v0.5 - Subvolumes

* btrfs-subvolume-tree
* ...

### v0.xyz

* ...

### v1.0
* At least get it into Debian Stretch in time

### Research / Ideas
* What's the difference of operating on a mounted filesystem using kernel
  ioctls, or operating on block devices directly?
