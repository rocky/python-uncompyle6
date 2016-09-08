# python 3.2 configparser.py

# Bug was emitting in 3.2
# def __init__(self, defaults=delimiters=('=', ':'),
#            comment_prefixes=('#', ';'), inline_comment_prefixes=None,
#            strict=True, empty_lines_in_values=True,
#            default_section=DEFAULTSECT, interpolation=_UNSET, dict_type=None,
#            allow_no_value=_default_dict, *, delimiters=('=', ':'),
#            comment_prefixes=('#', ';'), inline_comment_prefixes=None,
#            strict=True, empty_lines_in_values=True,
#            default_section=DEFAULTSECT,
#            interpolation=_UNSET):

def __init__(self, defaults=None, dict_type=_default_dict,
             allow_no_value=False, *, delimiters=('=', ':'),
             comment_prefixes=('#', ';'), inline_comment_prefixes=None,
             strict=True, empty_lines_in_values=True,
             default_section=DEFAULTSECT,
             interpolation=_UNSET):
    pass
