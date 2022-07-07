#  Copyright (c) 2022 Rocky Bernstein
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


def joined_str_ok(self, lhs, n, rule, tree, tokens, first, last):
    # In Python 3.8, there is a new "=" specifier.
    # See https://docs.python.org/3/whatsnew/3.8.html#f-strings-support-for-self-documenting-expressions-and-debugging
    # We detect this here inside joined_str by looking for an
    # expr->LOAD_STR which has an "=" added at the end
    # and is equal without the "=" to expr->formated_value2->LOAD_CONST
    # converted to a string.
    expr1 = tree[0]
    if expr1 != "expr":
        return False
    load_str = expr1[0]
    if load_str != "LOAD_STR":
        return False
    format_value_equal = load_str.attr
    if format_value_equal[-1] != "=":
        return False
    expr2 = tree[1]
    if expr2 != "expr":
        return False
    formatted_value = expr2[0]
    if not formatted_value.kind.startswith("formatted_value"):
        return False
    expr2a = formatted_value[0]
    if expr2a != "expr":
        return False
    load_const = expr2a[0]
    if load_const == "LOAD_CONST":
        format_value2 = load_const.attr
        return str(format_value2) == format_value_equal[:-1]
    return True
