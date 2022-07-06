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


def whilestmt38_check(
    self, lhs: str, n: int, rule, ast, tokens: list, first: int, last: int
) -> bool:
    # When we are missing a COME_FROM_LOOP, the
    # "while" statement is nested inside an if/else
    # so after the POP_BLOCK we have a JUMP_FORWARD which forms the "else" portion of the "if"
    # Check this.
    # print("XXX", first, last, rule)
    # for t in range(first, last):
    #     print(tokens[t])
    # print("=" * 40)

    if tokens[last] != "COME_FROM" and tokens[last - 1] == "COME_FROM":
        last -= 1
    if tokens[last - 1].kind.startswith("RAISE_VARARGS"):
        return True
    while tokens[last] == "COME_FROM":
        last -= 1
    # In a "while" loop, (in contrast to "for" loop), the loop jump is
    # always to the first offset
    first_offset = tokens[first].off2int()
    if tokens[last] == "JUMP_LOOP" and (
        tokens[last].attr == first_offset or tokens[last - 1].attr == first_offset
    ):
        return False
    return True
