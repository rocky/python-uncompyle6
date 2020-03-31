#  Copyright (c) 2018, 2020 by Rocky Bernstein
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
import uncompyle6.parser as python_parser


class ParserError(python_parser.ParserError):
    def __init__(self, error, tokens, debug):
        self.error = error  # previous exception
        self.tokens = tokens
        self.debug = debug

    def __str__(self):
        lines = ["--- This code section failed: ---"]
        if self.debug:
            lines.extend([t.format(token_num=i + 1) for i, t in enumerate(self.tokens)])
        else:
            lines.extend([t.format() for t in self.tokens])
        lines.extend(["", str(self.error)])
        return "\n".join(lines)
