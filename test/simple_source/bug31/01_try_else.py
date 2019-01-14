# Bug based on 2.7 test_itertools.py but mis-decompiled in Python 3.x bytecode
# The bug is confusing "try/else" with "try" as a result of the loop which causes
# the end of the except to jump back to the beginning of the loop, outside of the
# try. In 3.x we not distinguising this jump out of the loop with a jump to the
# end of the "try".

# RUNNABLE!
def testit(stmts):

    # Bug was confusing When the except jumps back to the beginning of the block
    # to the beginning of this for loop
    x = 1
    results = []
    for stmt in stmts:
        try:
            x = eval(stmt)
        except SyntaxError:
            results.append(1)
        else:
            results.append(x)
    return results

results = testit(["1 + 2", "1 +"])
assert results == [3, 1], "try with else failed"
