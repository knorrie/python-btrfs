# Copyright (C) 2016-2017 Hans van Kranenburg <hans@knorrie.org>
#
# This file is part of the python-btrfs module.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License v2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

import sys
if sys.version_info.major < 3:
    raise ImportError("This library is not compatible with Python 2 any more, sorry.")

from btrfs.ctree import FileSystem  # noqa
from btrfs.ctree import (  # noqa
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_TYPE_MASK,
    BLOCK_GROUP_RAID0, BLOCK_GROUP_RAID1, BLOCK_GROUP_RAID5,
    BLOCK_GROUP_RAID6, BLOCK_GROUP_DUP, BLOCK_GROUP_RAID10,
    BLOCK_GROUP_SINGLE, BLOCK_GROUP_PROFILE_MASK,
)
import btrfs.ctree  # noqa
import btrfs.ioctl  # noqa
from btrfs.ioctl import (  # noqa
    FEATURE_COMPAT_RO_FREE_SPACE_TREE,
    FEATURE_COMPAT_RO_FREE_SPACE_TREE_VALID,
    FEATURE_INCOMPAT_MIXED_BACKREF,
    FEATURE_INCOMPAT_DEFAULT_SUBVOL,
    FEATURE_INCOMPAT_MIXED_GROUPS,
    FEATURE_INCOMPAT_COMPRESS_LZO,
    FEATURE_INCOMPAT_COMPRESS_ZSTD,
    FEATURE_INCOMPAT_BIG_METADATA,
    FEATURE_INCOMPAT_EXTENDED_IREF,
    FEATURE_INCOMPAT_RAID56,
    FEATURE_INCOMPAT_SKINNY_METADATA,
    FEATURE_INCOMPAT_NO_HOLES,
)
import btrfs.utils  # noqa
import btrfs.crc32c  # noqa
import btrfs.free_space_tree  # noqa
