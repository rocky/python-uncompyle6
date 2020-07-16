#  Copyright (c) 2020 Rocky Bernstein

def aug_assign1_check(self, lhs, n, rule, ast, tokens, first, last):
    # print("XXX", first, last, rule)
    # for t in range(first, last): print(tokens[t])
    # print("="*40)

    expr = ast[0]
    return expr == "expr" and expr[0] == "or"
    return False
