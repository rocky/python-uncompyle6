# Bug from 3.3 configparser.py
# Python 3.3 has in bytecode positional args after keyoard args
# Python 3.4+ has positional args before keyword args
def __init__(self, defaults=None, dict_type=_default_dict,
             allow_no_value=False, *, delimiters=('=', ':'),
             comment_prefixes=('#', ';'), inline_comment_prefixes=None,
             strict=True, empty_lines_in_values=True,
             default_section=DEFAULTSECT,
             interpolation=_UNSET):
    pass

# From 3.5 sqlalchemy/orm/__init__.py
# Python 3.5 changes the stack position of where * args are (furthest down the stack)
# Python 3.6+ replaces CALL_FUNCTION_VAR_KW with CALL_FUNCTION_EX
def deferred(*columns, **kw):
    return ColumnProperty(deferred=True, *columns, **kw)


# From sqlalchemy/sql/selectable.py
class GenerativeSelect():
    def __init__(self,
                 ClauseList,
                 util,
                 order_by=None):
        self._order_by_clause = ClauseList(
            *util.to_list(order_by),
            _literal_as_text=5)
