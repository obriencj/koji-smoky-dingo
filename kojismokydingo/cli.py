# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


"""
Koji Smoky Dingo entry_point CLI hooks.

This module is merely a convenience for organizing the entry_point
hooks.

author: Christopher O'Brien <obriencj@gmail.com>
license: GPL v3
"""


from .affected_targets import AffectedTargets as affected_targets
from .mass_tag import BulkTagBuilds as bulk_tag_builds
from .check_hosts import CheckHosts as check_hosts
from .client_config import ClientConfig as client_config
from .identify_imported import ListImported as list_imported
from .list_archives import LatestArchives as latest_archives
from .list_archives import ListBuildArchives as list_build_archives
from .perminfo import PermissionInfo as perminfo
from .renum_tag import RenumTagInheritance as renum_tag_inheritance
from .swap_inheritance import SwapTagInheritance as swap_tag_inheritance
from .userinfo import UserInfo as userinfo


CLI = (
    affected_targets,
    bulk_tag_builds,
    check_hosts,
    client_config,
    list_imported,
    latest_archives,
    list_build_archives,
    perminfo,
    renum_tag_inheritance,
    swap_tag_inheritance,
    userinfo,
)


#
# The end.
