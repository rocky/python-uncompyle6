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
