"""
Python parse tree checker.

Our rules sometimes give erroneous results. Until we have perfect rules,
This checker will catch mistakes in decompilation we've made.

FIXME idea: extend parsing system to do same kinds of checks or nonterminal
before reduction and don't reduce when there is a problem.
"""


def checker(ast, in_loop, errors):
    if ast is None:
        return
    in_loop = (
        in_loop
        or ast.kind.startswith("for")
        or ast.kind.startswith("while")
        or ast.kind.startswith("async_for")
    )
    if ast.kind in ("aug_assign1", "aug_assign2") and ast[0][0] == "and":
        text = str(ast)
        error_text = (
            "\n# improper augmented assignment (e.g. +=, *=, ...):\n#\t"
            + "\n# ".join(text.split("\n"))
            + "\n"
        )
        errors.append(error_text)

    for node in ast:
        if not in_loop and node.kind in ("continue", "break"):
            text = str(node)
            error_text = "\n# not in loop:\n#\t" + "\n# ".join(text.split("\n"))
            errors.append(error_text)
        if hasattr(node, "__repr1__"):
            checker(node, in_loop, errors)
