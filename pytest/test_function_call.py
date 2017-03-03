# std
import string
# 3rd party
from hypothesis import strategies as st
from hypothesis import given, assume
# uncompyle
from validate import validate_uncompyle


alpha = st.sampled_from(string.ascii_lowercase)
numbers = st.sampled_from(string.digits)
alphanum = st.sampled_from(string.ascii_lowercase + string.digits)
expressions = st.sampled_from([x for x in string.ascii_lowercase + string.digits] + ['x+1'])


@st.composite
def function_calls(draw):
    """
    Strategy factory for generating function calls.

    :param draw: Callable which draws examples from other strategies.

    :return: The function call text.
    """
    positional_args = draw(st.lists(alphanum, min_size=0, max_size=3))
    named_args = [x + '=0' for x in draw(st.lists(alpha, min_size=0, max_size=3))]
    star_args = ['*' + x for x in draw(st.lists(alpha, min_size=0, max_size=1))]
    double_star_args = ['**' + x for x in draw(st.lists(alpha, min_size=0, max_size=1))]

    arguments = positional_args + named_args + star_args + double_star_args
    draw(st.randoms()).shuffle(arguments)
    arguments = ','.join(arguments)

    function_call = 'fn({arguments})'.format(arguments=arguments)
    try:
        # TODO: Figure out the exact rules for ordering of positional named,
        # star args and double star args and in which versions the various
        # types of arguments are supported so we don't need to check that the
        # expression compiles like this.
        compile(function_call, '<string>', 'single')
    except:
        assume(False)
    return function_call


@given(function_calls())
def test_function_call(function_call):
    validate_uncompyle(function_call)
