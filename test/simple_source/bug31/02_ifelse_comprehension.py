# Python 2.7 sqlalchemy-1.013/sql/crud.py
def _extend_values_for_multiparams(compiler, stmt, c):
    c(
        [
            (
                (compiler() if compiler()
                    else compiler())
                if c in stmt else compiler(),
            )
        ]
        for i in enumerate(stmt)
    )
