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
"""Isolate Python 3.7 version-specific semantic actions here.
"""

from uncompyle6.semantics.consts import PRECEDENCE, TABLE_DIRECT

def customize_for_version37(self, version):
    ########################
    # Python 3.7+ changes
    #######################

    PRECEDENCE['attribute37'] =  2
    PRECEDENCE['if_exp_37a']   = 28
    PRECEDENCE['if_exp_37b']   = 28

    TABLE_DIRECT.update({
        'and_not':  ( '%c and not %c',
                      (0, 'expr'), (2, 'expr') ),
        'async_forelse_stmt':  (
            '%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
            (7, 'store'), (1, 'expr'), (17, 'for_block'), (25, 'else_suite') ),
        'async_for_stmt':  (
            '%|async for %c in %c:\n%+%c%-\n\n',
            (7, 'store'), (1, 'expr'), (17, 'for_block')),
        'async_for_stmt37':  (
            '%|async for %c in %c:\n%+%c%-%-\n\n',
            (7, 'store'), (1, 'expr'), (16, 'for_block') ),
        'attribute37':  ( '%c.%[1]{pattr}', 0 ),
        'compare_chained1a_37': (
            ' %[3]{pattr.replace("-", " ")} %p %p',
            (0, 19), (-4, 19)),
        'compare_chained1_false_37': (
            ' %[3]{pattr.replace("-", " ")} %p %p',
            (0, 19), (-4, 19)),
        'compare_chained2_false_37': (
            ' %[3]{pattr.replace("-", " ")} %p %p',
            (0, 19), (-5, 19)),
        'compare_chained1b_37': (
            ' %[3]{pattr.replace("-", " ")} %p %p',
            (0, 19), (-4, 19)),
        'compare_chained1c_37': (
            ' %[3]{pattr.replace("-", " ")} %p %p',
            (0, 19), (-2, 19)),
        'compare_chained2a_37': (
            '%[1]{pattr.replace("-", " ")} %p',
            (0, 19) ),
        'compare_chained2b_37': (
            '%[1]{pattr.replace("-", " ")} %p',
            (0, 19) ),
        'compare_chained2a_false_37': (
            '%[1]{pattr.replace("-", " ")} %p',
            (0, 19 ) ),
        'compare_chained2c_37': (
            '%[3]{pattr.replace("-", " ")} %p %p', (0, 19), (6, 19) ),
        'if_exp_37a': ( '%p if %p else %p', (1, 'expr', 27), (0, 27), (4, 'expr', 27) ),
        'if_exp_37b': ( '%p if %p else %p', (2, 'expr', 27), (0, 'expr', 27), (5, 'expr', 27) ),
        'testfalse_not_or': ( "not %c or %c",
                              (0, "expr"),
                              (2, "expr")  ),
        'testfalse_not_and': ( "not (%c)", 0 ),

        })
