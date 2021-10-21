#  Copyright (c) 2020 Rocky Bernstein

def except_handler(self, lhs, n, rule, ast, tokens, first, last):
    end_token = tokens[last-1]

    # print("XXX", first, last)
    # for t in range(first, last):
    #     print(tokens[t])
    # print("=" * 30)

    # FIXME: Figure out why this doesn't work on
    # bytecode-1.4/anydbm.pyc
    if self.version[:2] == (1, 4):
        return False

    # Make sure come froms all come from within "except_handler".
    if end_token != "COME_FROM":
        return False
    return end_token.attr < tokens[first].offset
