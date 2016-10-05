python-btrfs roadmap
====================

### v0.3 - More data structures

* based on extents, list files that use them (fs tree, inodes) (with full path)
* subvolumes and the fs tree, directories, files, inodes, etc
* Fix ioctl handling so it doesn't generate garbage for != amd64 see ba03a99a9

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
