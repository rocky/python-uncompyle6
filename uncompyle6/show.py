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
            stream.write('\n')


def maybe_show_tree(show_tree, ast):
    """
    Show the ast based on the showast flag (or file object), writing to the
    appropriate stream depending on the type of the flag.

    :param show_tree: Flag which determines whether the parse tree is
                      written to sys.stdout or not. (It is also to pass a file
                      like object, into which the ast will be written).
    :param ast:     The ast to show.
    """
    if show_tree:
        if hasattr(show_tree, 'write'):
            stream = show_tree
        else:
            stream = sys.stdout
        stream.write(str(ast))
        stream.write('\n')


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
        stream.write('\n')
        stream.write('--')
        stream.write('\n')
