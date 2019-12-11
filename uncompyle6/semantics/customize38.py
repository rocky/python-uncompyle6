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
"""Isolate Python 3.8 version-specific semantic actions here.
"""

########################
# Python 3.8+ changes
#######################

from uncompyle6.semantics.consts import TABLE_DIRECT

def customize_for_version38(self, version):

    # FIXME: pytest doesn't add proper keys in testing. Reinstate after we have fixed pytest.
    # for lhs in 'for forelsestmt forelselaststmt '
    #             'forelselaststmtl tryfinally38'.split():
    #     del TABLE_DIRECT[lhs]

    TABLE_DIRECT.update({
        'async_for_stmt38':  (
            '%|async for %c in %c:\n%+%c%-%-\n\n',
            (7, 'store'), (0, 'expr'), (8, 'for_block') ),

        'async_forelse_stmt38':  (
            '%|async for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
            (7, 'store'), (0, 'expr'), (8, 'for_block'), (-1, 'else_suite') ),

        'async_with_stmt38': (
            '%|async with %c:\n%+%|%c%-',
            (0, 'expr'), 7),

        'async_with_as_stmt38':  (
            '%|async with %c as %c:\n%+%|%c%-',
            (0, 'expr'), (6, 'store'),
            (7, 'suite_stmts') ),

        'except_handler38': (
            '%c', (2, 'except_stmts') ),

        'except_handler38a': (
            '%c', (-2, 'stmts') ),

        'except_ret38a': (
            'return %c', (4, 'expr') ),

        # Note: there is a suite_stmts_opt which seems
        # to be bookkeeping which is not expressed in source code
        'except_ret38':  ( '%|return %c\n', (1, 'expr') ),

        'for38':            (
            '%|for %c in %c:\n%+%c%-\n\n',
            (2, 'store'),
            (0, 'expr'),
            (3, 'for_block') ),
        'forelsestmt38':    (
            '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
            (2, 'store'),
            (0, 'expr'),
            (3, 'for_block'), -2 ),
        'forelselaststmt38': (
            '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-',
            (2, 'store'),
            (0, 'expr'),
            (3, 'for_block'), -2 ),
        'forelselaststmtl38':	(
            '%|for %c in %c:\n%+%c%-%|else:\n%+%c%-\n\n',
            (2, 'store'),
            (0, 'expr'),
            (3, 'for_block'), -2 ),

        'ifpoplaststmtl': ( '%|if %c:\n%+%c%-',
                            (0, "testexpr"),
                            (2, "c_stmts" ) ),

        'ifstmtl':	  ( '%|if %c:\n%+%c%-',
                            (0, "testexpr"),
                            (1, "_ifstmts_jumpl") ),

        'whilestmt38': ( '%|while %c:\n%+%c%-\n\n',
                         (1, 'testexpr'),
                         2 ), # "l_stmts" or "pass"
        'whileTruestmt38': ( '%|while True:\n%+%c%-\n\n',
                             1 ), # "l_stmts" or "pass"
        'try_elsestmtl38': (
            '%|try:\n%+%c%-%c%|else:\n%+%c%-',
            (1, 'suite_stmts_opt'),
            (3, 'except_handler38'),
            (5, 'else_suitel') ),
        'try_except38': (
            '%|try:\n%+%c\n%-%|except:\n%|%-%c\n\n',
                   (-2, 'suite_stmts_opt'), (-1, 'except_handler38a') ),
        'try_except_ret38': (
            '%|try:\n%+%|return %c%-\n%|except:\n%+%|%c%-\n\n',
                   (1, 'expr'), (-1, 'except_ret38a') ),
        'tryfinally38rstmt': (
            '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n',
                   (3, 'returns'), 6 ),
        'tryfinally38stmt': (
            '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n',
            (1, "suite_stmts_opt"),
            (6, "suite_stmts_opt") ),
        'tryfinally38astmt': (
            '%|try:\n%+%c%-%|finally:\n%+%c%-\n\n',
            (2, "suite_stmts_opt"),
            (8, "suite_stmts_opt") ),
        "named_expr": ( # AKA "walrus operator"
            "%c := %c", (2, "store"), (0, "expr")
            )
    })
