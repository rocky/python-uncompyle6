#  Copyright (c) 2019-2020 by Rocky Bernstein
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
"""Isolate Python 2.5+ version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import TABLE_DIRECT


#######################
# Python 2.5+ Changes #
#######################
def customize_for_version25(self, version):
    ########################
    # Import style for 2.5+
    ########################
    TABLE_DIRECT.update(
        {
            "importmultiple": ("%|import %c%c\n", 2, 3),
            "import_cont": (", %c", 2),
            # With/as is allowed as "from future" thing in 2.5
            # Note: It is safe to put the variables after "as" in parenthesis,
            # and sometimes it is needed.
            "with": ("%|with %c:\n%+%c%-", 0, 3),
            "and_then": ("%c and %c", (0, "expr"), (4, "expr")),
        }
    )

    # In 2.5+ "except" handlers and the "finally" can appear in one
    # "try" statement. So the below has the effect of combining the
    # "tryfinally" with statement with the "try_except" statement.
    # FIXME: something doesn't smell right, since the semantics
    # are different. See test_fileio.py for an example that shows this.
    def tryfinallystmt(node):
        if len(node[1][0]) == 1 and node[1][0][0] == "stmt":
            if node[1][0][0][0] == "try_except":
                node[1][0][0][0].kind = "tf_try_except"
            if node[1][0][0][0] == "tryelsestmt":
                node[1][0][0][0].kind = "tf_tryelsestmt"
        self.default(node)

    self.n_tryfinallystmt = tryfinallystmt

    def n_import_from(node):
        if node[0].pattr > 0:
            node[2].pattr = ("." * node[0].pattr) + node[2].pattr
        self.default(node)

    self.n_import_from = n_import_from
