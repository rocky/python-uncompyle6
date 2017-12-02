# Had bug in Python 3.x

# Should see (Python 2.x and 3.x:
# get_iter ::= expr GET_ITER
# expr ::= get_iter
# _for ::= GET_ITER FOR_ITER
# store ::= STORE_FAST
# expr ::= LOAD_FAST
# yield ::= expr YIELD_VALUE
# expr ::= yield
# gen_comp_body ::= expr YIELD_VALUE POP_TOP
# comp_body ::= gen_comp_body
# comp_iter ::= comp_body
# comp_for ::= expr _for store comp_iter JUMP_BACK
# comp_iter ::= comp_for
# genexpr_func ::= LOAD_FAST FOR_ITER store comp_iter JUMP_BACK

def multi_genexpr(blog_posts):

    return (
        entry
        for blog_post in blog_posts
        for entry in blog_post.entry_set
    )
