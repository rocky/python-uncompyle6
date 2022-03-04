# Copyright (C) 2018, 2020 Rocky Bernstein <rocky@gnu.org>
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
import sys


def maybe_show_asm(showasm, tokens):
    """
    Show the asm based on the showasm flag (or file object), writing to the
    appropriate stream depending on the type of the flag.

    :param showasm: Flag which determines whether the ingested code is
                    written to sys.stdout or not. (It is also to pass a file
                    like object, into which the asm will be written).
    :param tokens:  The asm tokens to show.
    """
    if showasm:
        if hasattr(showasm, 'write'):
            stream = showasm
        else:
            stream = sys.stdout
        for t in tokens:
            stream.write(str(t))
            stream.write("\n")


def maybe_show_tree(walker, ast):
    """
    Show the ast based on the showast flag (or file object), writing to the
    appropriate stream depending on the type of the flag.

    :param show_tree: Flag which determines whether the parse tree is
                      written to sys.stdout or not. (It is also to pass a file
                      like object, into which the ast will be written).
    :param ast:     The ast to show.
    """
    if walker.showast:
        if hasattr(walker.showast, "write"):
            stream = walker.showast
        else:
            stream = sys.stdout
        if (
            isinstance(walker.showast, dict)
            and walker.showast.get("after", False)
            and hasattr(walker, "str_with_template")
        ):
            walker.str_with_template(ast)
        else:
            stream.write(str(ast))
        stream.write("\n")


def maybe_show_tree_param_default(show_tree, name, default):
    """
    Show a function parameter with default for an grammar-tree based on the show_tree flag
    (or file object), writing to the appropriate stream depending on the type
    of the flag.

    :param show_tree: Flag which determines whether the function parameter with
                      default is written to sys.stdout or not. (It is also to
                      pass a file like object, into which the ast will be
                      written).
    :param name:    The function parameter name.
    :param default: The function parameter default.
    """
    if show_tree:
        if hasattr(show_tree, 'write'):
            stream = show_tree
        else:
            stream = sys.stdout
        stream.write('\n')
        stream.write('--' + name)
        stream.write('\n')
        stream.write(str(default))
        stream.write("\n")
        stream.write("--")
        stream.write("\n")
