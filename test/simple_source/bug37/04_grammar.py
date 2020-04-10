# From test_grammar.py
# RUNNABLE!
def check_syntax_error(statement):
    try:
        compile(statement, '<test string>', 'exec')
    except SyntaxError:
        return
    assert False

def test_yield():
    # Requires parentheses as call argument
    def g():
        f((yield 1), 1)
    def g():
        f((yield from ()))
    def g():
        f((yield from ()), 1)
    def g():
        f((yield 1))

    # Allowed as standalone statement
    def g():
        yield 1

    def g():
        yield from ()

    # Allowed as RHS of assignment
    def g():
        x = yield 1

    def g():
        x = yield from ()

    # Ordinary yield accepts implicit tuples
    def g():
        yield 1, 1

    def g():
        x = yield 1, 1

    # 'yield from' does not
    check_syntax_error("def g(): yield from (), 1")
    check_syntax_error("def g(): x = yield from (), 1")
    # Requires parentheses as subexpression
    def g():
        1, (yield 1)

    def g():
        1, (yield from ())

    check_syntax_error("def g(): 1, yield 1")
    check_syntax_error("def g(): 1, yield from ()")
    # Requires parentheses as call argument
    def g():
        f((yield 1))

    def g():
        f((yield 1), 1)

    def g():
        f((yield from ()))

    def g():
        f((yield from ()), 1)

    check_syntax_error("def g(): f(yield 1)")
    check_syntax_error("def g(): f(yield 1, 1)")
    check_syntax_error("def g(): f(yield from ())")
    check_syntax_error("def g(): f(yield from (), 1)")
    # Not allowed at top level
    check_syntax_error("yield")
    check_syntax_error("yield from")
    # Not allowed at class scope
    check_syntax_error("class foo:yield 1")
    check_syntax_error("class foo:yield from ()")
    # Check annotation refleak on SyntaxError
    check_syntax_error("def g(a:(yield)): pass")

test_yield()

# From test_types.py
# Bug was needing parens around (yield 2)
def gen_func():
    yield 1
    return (yield 2)
gen = gen_func()
