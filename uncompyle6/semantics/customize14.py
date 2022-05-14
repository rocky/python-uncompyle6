#  Copyright (c) 2022 by Rocky Bernstein
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Isolate Python 1.4- version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import TABLE_DIRECT

#######################
# Python 1.4- Changes #
#######################
def customize_for_version14(self, version):
    TABLE_DIRECT.update(
        {
            "print_expr_stmt": (
                ("%|print %c\n", 0)
            ),
        }
    )
