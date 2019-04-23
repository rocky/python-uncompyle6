#  Copyright (c) 2019 by Rocky Bernstein
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
"""Isolate Python 2.6 and 2.7 version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import TABLE_DIRECT

def customize_for_version26_27(self, version):

    ########################################
    # Python 2.6+
    #    except <condition> as <var>
    # vs. older:
    #    except <condition> , <var>
    #
    # For 2.6 we use the older syntax which
    # matches how we parse this in bytecode
    ########################################
    if version > 2.6:
        TABLE_DIRECT.update({
            'except_cond2':	( '%|except %c as %c:\n', 1, 5 ),
        })
    else:
        TABLE_DIRECT.update({
            'testtrue_then': ( 'not %p', (0, 22) ),

        })
