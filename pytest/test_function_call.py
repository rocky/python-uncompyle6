# std
import string
# 3rd party
from hypothesis import given, assume, strategies as st
import pytest
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
    list1 = st.lists(alpha, min_size=0, max_size=1)
    list3 = st.lists(alpha, min_size=0, max_size=3)

    positional_args = draw(list3)
    named_args = [x + '=0' for x in draw(list3)]
    star_args = ['*' + x for x in draw(list1)]
    double_star_args = ['**' + x for x in draw(list1)]

    arguments = positional_args + named_args + star_args + double_star_args
    draw(st.randoms()).shuffle(arguments)
    arguments = ','.join(arguments)

    function_call = 'fn({arguments})'.format(arguments=arguments)
    try:
        # TODO: Figure out the exact rules for ordering of positional, named,
        # star args, double star args and in which versions the various
        # types of arguments are supported so we don't need to check that the
        # expression compiles like this.
        compile(function_call, '<string>', 'single')
    except:
        assume(False)
    return function_call


@pytest.mark.xfail()
def test_CALL_FUNCTION():
    validate_uncompyle("fn(w,m,f)")


@pytest.mark.xfail()
def test_BUILD_CONST_KEY_MAP_BUILD_MAP_UNPACK_WITH_CALL_BUILD_TUPLE_CALL_FUNCTION_EX():
    validate_uncompyle("fn(w=0,m=0,**v)")


@pytest.mark.xfail()
def test_BUILD_MAP_BUILD_MAP_UNPACK_WITH_CALL_BUILD_TUPLE_CALL_FUNCTION_EX():
    validate_uncompyle("fn(a=0,**g)")


@pytest.mark.xfail()
def test_CALL_FUNCTION_KW():
    validate_uncompyle("fn(j=0)")


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


examples = set()
generate_examples = False


@pytest.mark.skipif(not generate_examples, reason='not generating examples')
@given(function_calls())
def test_generate_hypothesis(function_call):
    examples.add(function_call)


@pytest.mark.skipif(not generate_examples, reason='not generating examples')
def test_generate_examples():
    import dis
    example_opcodes = {}
    for example in examples:
        opcodes = tuple(sorted(set(
            instruction.opname
            for instruction in dis.Bytecode(example)
            if instruction.opname not in ('LOAD_CONST', 'LOAD_NAME', 'RETURN_VALUE')
        )))
        example_opcodes[opcodes] = example
    for k, v in example_opcodes.items():
        print('def test_' + '_'.join(k) + '():\n    validate_uncompyle("' + v + '")\n\n')
    return
