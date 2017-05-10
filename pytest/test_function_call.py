# std
import string
# 3rd party
from hypothesis import given, assume, example, settings, strategies as st
import pytest
# uncompyle
from validate import validate_uncompyle
from test_fstring import expressions


alpha = st.sampled_from(string.ascii_lowercase)
numbers = st.sampled_from(string.digits)
alphanum = st.sampled_from(string.ascii_lowercase + string.digits)


@st.composite
def function_calls(draw,
                   min_keyword_args=0, max_keyword_args=5,
                   min_positional_args=0, max_positional_args=5,
                   min_star_args=0, max_star_args=1,
                   min_double_star_args=0, max_double_star_args=1):
    """
    Strategy factory for generating function calls.

    :param draw: Callable which draws examples from other strategies.

    :return: The function call text.
    """
    st_positional_args = st.lists(
        alpha,
        min_size=min_positional_args,
        max_size=max_positional_args
    )
    st_keyword_args = st.lists(
        alpha,
        min_size=min_keyword_args,
        max_size=max_keyword_args
    )
    st_star_args = st.lists(
        alpha,
        min_size=min_star_args,
        max_size=max_star_args
    )
    st_double_star_args = st.lists(
        alpha,
        min_size=min_double_star_args,
        max_size=max_double_star_args
    )

    positional_args = draw(st_positional_args)
    keyword_args = draw(st_keyword_args)
    st_values = st.lists(
        expressions(),
        min_size=len(keyword_args),
        max_size=len(keyword_args)
    )
    keyword_args = [
        x + '=' + e
        for x, e in
        zip(keyword_args, draw(st_values))
    ]
    star_args = ['*' + x for x in draw(st_star_args)]
    double_star_args = ['**' + x for x in draw(st_double_star_args)]

    arguments = positional_args + keyword_args + star_args + double_star_args
    draw(st.randoms()).shuffle(arguments)
    arguments = ','.join(arguments)

    function_call = 'fn({arguments})'.format(arguments=arguments)
    try:
        # TODO: Figure out the exact rules for ordering of positional, keyword,
        # star args, double star args and in which versions the various
        # types of arguments are supported so we don't need to check that the
        # expression compiles like this.
        compile(function_call, '<string>', 'single')
    except:
        assume(False)
    return function_call


def test_function_no_args():
    validate_uncompyle("fn()")


def isolated_function_calls(which):
    """
    Returns a strategy for generating function calls, but isolated to 
    particular types of arguments, for example only positional arguments.

    This can help reason about debugging errors in specific types of function
    calls.

    :param which: One of 'keyword', 'positional', 'star', 'double_star'

    :return: Strategy for generating an function call isolated to specific
             argument types.
    """
    kwargs = dict(
        max_keyword_args=0,
        max_positional_args=0,
        max_star_args=0,
        max_double_star_args=0,
    )
    kwargs['_'.join(('min', which, 'args'))] = 1
    kwargs['_'.join(('max', which, 'args'))] = 5 if 'star' not in which else 1
    return function_calls(**kwargs)


with settings(max_examples=25):

    @given(isolated_function_calls('positional'))
    @example("fn(0)")
    def test_function_positional_only(expr):
        validate_uncompyle(expr)

    @given(isolated_function_calls('keyword'))
    @example("fn(a=0)")
    def test_function_call_keyword_only(expr):
        validate_uncompyle(expr)

    @given(isolated_function_calls('star'))
    @example("fn(*items)")
    def test_function_call_star_only(expr):
        validate_uncompyle(expr)

    @given(isolated_function_calls('double_star'))
    @example("fn(**{})")
    def test_function_call_double_star_only(expr):
        validate_uncompyle(expr)


@pytest.mark.xfail()
def test_BUILD_CONST_KEY_MAP_BUILD_MAP_UNPACK_WITH_CALL_BUILD_TUPLE_CALL_FUNCTION_EX():
    validate_uncompyle("fn(w=0,m=0,**v)")


@pytest.mark.xfail()
def test_BUILD_MAP_BUILD_MAP_UNPACK_WITH_CALL_BUILD_TUPLE_CALL_FUNCTION_EX():
    validate_uncompyle("fn(a=0,**g)")


@pytest.mark.xfail()
def test_CALL_FUNCTION_EX():
    validate_uncompyle("fn(*g,**j)")


@pytest.mark.xfail()
def test_BUILD_MAP_CALL_FUNCTION_EX():
    validate_uncompyle("fn(*z,u=0)")


@pytest.mark.xfail()
def test_BUILD_TUPLE_CALL_FUNCTION_EX():
    validate_uncompyle("fn(**a)")


@pytest.mark.xfail()
def test_BUILD_MAP_BUILD_TUPLE_BUILD_TUPLE_UNPACK_WITH_CALL_CALL_FUNCTION_EX():
    validate_uncompyle("fn(b,b,b=0,*a)")


@pytest.mark.xfail()
def test_BUILD_TUPLE_BUILD_TUPLE_UNPACK_WITH_CALL_CALL_FUNCTION_EX():
    validate_uncompyle("fn(*c,v)")


@pytest.mark.xfail()
def test_BUILD_CONST_KEY_MAP_CALL_FUNCTION_EX():
    validate_uncompyle("fn(i=0,y=0,*p)")


@pytest.mark.skip(reason='skipping property based test until all individual tests are passing')
@given(function_calls())
def test_function_call(function_call):
    validate_uncompyle(function_call)
