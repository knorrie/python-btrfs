# Copyright (C) 2016 Hans van Kranenburg <hans@knorrie.org>
#
# This file is part of the python-btrfs module.
#
# python-btrfs is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-btrfs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with python-btrfs.  If not, see <http://www.gnu.org/licenses/>.

import inspect
import sys
if sys.version_info.major < 3:
    raise ImportError("This library is not compatible with Python 2 any more, sorry.")


from btrfs.ctree import FileSystem  # noqa
from btrfs.ctree import (  # noqa
    BLOCK_GROUP_DATA, BLOCK_GROUP_SYSTEM, BLOCK_GROUP_METADATA,
    SPACE_INFO_GLOBAL_RSV, BLOCK_GROUP_TYPE_MASK,
    BLOCK_GROUP_RAID0, BLOCK_GROUP_RAID1, BLOCK_GROUP_RAID5,
    BLOCK_GROUP_RAID1C3, BLOCK_GROUP_RAID1C4,
    BLOCK_GROUP_RAID6, BLOCK_GROUP_DUP, BLOCK_GROUP_RAID10,
    BLOCK_GROUP_SINGLE, BLOCK_GROUP_PROFILE_MASK,
)
import btrfs.ctree  # noqa
import btrfs.ioctl  # noqa
import btrfs.utils  # noqa
import btrfs.crc32c  # noqa
import btrfs.free_space_tree  # noqa
import btrfs.volumes  # noqa
import btrfs.fs_usage  # noqa
from btrfs.version import __version__  # noqa


# Classes in our modules can define a _pretty_properties class method that
# returns hints for properties for the pretty printer that they want to have
# added dynamically.
#
# Each value in the list is a tuple containing two values:
# * The function that needs to be run to get the pretty string representation.
# * The name of the attribute whose value needs to be fed to that function.
#
# The helper functions and pretty printer itself can be found in btrfs.utils.
#
# After importing all modules, we look around for classes and gather all info.
def _generate_pretty_properties():
    def pretty_property_factory(cls, fn, attribute_name):
        def property_fn(self):
            return fn(getattr(self, attribute_name))
        return property_fn

    for module in [
        btrfs.ctree,
        btrfs.ioctl,
        btrfs.fs_usage,
    ]:
        for name, cls in inspect.getmembers(
            module,
            lambda member: inspect.isclass(member) and member.__module__ == module.__name__
        ):
            try:
                hints = cls._pretty_properties()
            except AttributeError:
                continue
            for fn, attribute_name in hints:
                setattr(cls, '{}_str'.format(attribute_name),
                        property(pretty_property_factory(cls, fn, attribute_name), None,
                                 doc="Pretty string representation for the {} attribute.".format(
                                     attribute_name)))


_generate_pretty_properties()
