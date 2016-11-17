"""
Python AST grammar checker.

Our rules sometimes give erroneous results. Until we have perfect rules,
This checker will catch mistakes in decompilation we've made.

FIXME idea: extend parsing system to do same kinds of checks or nonterminal
before reduction and don't reduce when there is a problem.
"""

def checker(ast, in_loop, errors):
    in_loop = in_loop or ast.type in ('while1stmt', 'whileTruestmt',
                                      'whilestmt', 'whileelsestmt',
                                      'for_block')
    if ast.type in ('augassign1', 'augassign2') and ast[0][0] == 'and':
        text = str(ast)
        error_text = '\n# improper augmented assigment (e.g. +=, *=, ...):\n#\t' + '\n# '.join(text.split("\n")) + '\n'
        errors.append(error_text)

    for node in ast:
        if not in_loop and node.type in ('continue_stmt', 'break_stmt'):
            text = str(node)
            error_text = '\n# not in loop:\n#\t' + '\n# '.join(text.split("\n"))
            errors.append(error_text)
        if hasattr(node, '__repr1__'):
            checker(node, in_loop, errors)
