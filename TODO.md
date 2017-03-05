python-btrfs roadmap
====================

### v(+1) - Integrate r/w metadata page handling

* Load metadata page blob, fix corruption, write it out again

Don't expose it too much yet, but make sure it can be done.  Part of the code
for doing this is already present in a WIP branch, and I want to get loose
things lying around gone first. Use python memoryviews to create r/w slices of
the whole page.

### v(+2) - Documentation

Target audience: sysadmin with a bit of programming knowledge that does not
want to parse output of btrfs xyz commands with regexes.

* Getting started!
* What's in the source code?
* Some more examples explained
* Clearly state which parts of the library are API-stable and which ones are not.

### v(+3) - More about subvolumes

* btrfs-subvolume-tree ?
* ...

### v0.xyz

* ...

### Research / Ideas / Distant Future (tm)
* What's the difference of operating on a mounted filesystem using kernel
  ioctls, or operating on block devices directly?
* Become an 'assisted hexedit' with superpowers for Btrfs filesystems
