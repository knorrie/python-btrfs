python-btrfs roadmap
====================

### v(+1) - More data structures

* based on extents, list files that use them (fs tree, inodes) (with full path)
* subvolumes and the fs tree, directories, files, inodes, etc
* Fix ioctl handling so it doesn't generate garbage for != amd64 see ba03a99a9

### v(+2) - Documentation

Target audience: sysadmin with a bit of programming knowledge that does not
want to parse output of btrfs xyz commands with regexes.

* Getting started!
* What's in the source code?
* Some more examples explained

### v(+3) - More about subvolumes

* btrfs-subvolume-tree
* ...

### v0.xyz

* ...

### Research / Ideas / Distant Future (tm)
* What's the difference of operating on a mounted filesystem using kernel
  ioctls, or operating on block devices directly?
* Become an 'assisted hexedit' with superpowers for Btrfs filesystems
