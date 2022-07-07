#  Copyright (c) 2020, 2022 Rocky Bernstein
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


def iflaststmt(
    self, lhs: str, n: int, rule, tree, tokens: list, first: int, last: int
) -> bool:
    testexpr = tree[0]

    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    if testexpr[0] in ("testtrue", "testfalse"):

        test = testexpr[0]
        if len(test) > 1 and test[1].kind.startswith("jmp_"):
            if last == n:
                last -= 1
            jmp_target = test[1][0].attr
            if tokens[first].off2int() <= jmp_target < tokens[last].off2int():
                return True
            # jmp_target less than tokens[first] is okay - is to a loop
            # jmp_target equal tokens[last] is also okay: normal non-optimized non-loop jump

            if (
                (last + 1) < n
                and tokens[last - 1] != "JUMP_BACK"
                and tokens[last + 1] == "COME_FROM_LOOP"
            ):
                # iflastsmtl is not at the end of a loop, but jumped outside of loop. No good.
                # FIXME: check that tokens[last] == "POP_BLOCK"? Or allow for it not to appear?
                return True

            # If the instruction before "first" is a "POP_JUMP_IF_FALSE" which goes
            # to the same target as jmp_target, then this not nested "if .. if .."
            # but rather "if ... and ..."
            if first > 0 and tokens[first - 1] == "POP_JUMP_IF_FALSE":
                return tokens[first - 1].attr == jmp_target

            if jmp_target > tokens[last].off2int():
                # One more weird case to look out for
                #   if c1:
                #      if c2:  # Jumps around the *outer* "else"
                #       ...
                #   else:
                if jmp_target == tokens[last - 1].attr:
                    return False
                if last < n and tokens[last].kind.startswith("JUMP"):
                    return False
                return True

        pass
    return False
