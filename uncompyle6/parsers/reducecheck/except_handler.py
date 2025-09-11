#  Copyright (c) 2020, 2025 Rocky Bernstein


def except_handler(self, lhs, n: int, rule, ast, tokens: list, first: int, last: int):
    end_token = tokens[last - 1]

    # print("XXX", first, last)
    # for t in range(first, last):
    #     print(tokens[t])
    # print("=" * 30)

    # FIXME: Figure out why this doesn't work on
    # bytecode-1.4/anydbm.pyc
    if self.version[:2] == (1, 4):
        return False

    # Make sure COME_FROMs froms come from within "except_handler".
    if end_token.kind != "COME_FROM":
        return False
    return end_token.attr is not None and end_token.attr < tokens[first].offset
