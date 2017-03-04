# std
import string
# 3rd party
from hypothesis import given, assume, example, strategies as st
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
@given(function_calls())
@example('fn(i,d)')                       # CALL_FUNCTION
@example('fn(*q)')                        # CALL_FUNCTION_EX
@example('fn(**n)')                       # BUILD_TUPLE, CALL_FUNCTION_EX
@example('fn(r=0)')                       # CALL_FUNCTION_KW
@example('fn(q=0,**f)')                   # BUILD_MAP, BUILD_MAP_UNPACK_WITH_CALL, BUILD_TUPLE, CALL_FUNCTION_EX
@example('fn(h,*b)')                      # BUILD_TUPLE, BUILD_TUPLE_UNPACK_WITH_CALL, CALL_FUNCTION_EX
@example('fn(*a,a=0)')                    # BUILD_MAP, CALL_FUNCTION_EX
@example('fn(**m,i=0,a=0,b=0)')           # BUILD_CONST_KEY_MAP, BUILD_MAP_UNPACK_WITH_CALL, BUILD_TUPLE, CALL_FUNCTION_EX
@example('fn(l=0,v=0,*e,f=0)')            # BUILD_CONST_KEY_MAP, CALL_FUNCTION_EX
@example('fn(*c,a=0,**t)')                # BUILD_MAP, BUILD_MAP_UNPACK_WITH_CALL, CALL_FUNCTION_EX
@example('fn(p=0,*a,n=0,a=0,**a)')        # BUILD_CONST_KEY_MAP, BUILD_MAP_UNPACK_WITH_CALL, CALL_FUNCTION_EX
@example('fn(l=0,**d,o=0,f=0)')           # BUILD_CONST_KEY_MAP, BUILD_MAP, BUILD_MAP_UNPACK_WITH_CALL, BUILD_TUPLE, CALL_FUNCTION_EX
@example('fn(t=0,s=0,*c,**f,g=0)')        # BUILD_CONST_KEY_MAP, BUILD_MAP, BUILD_MAP_UNPACK_WITH_CALL, CALL_FUNCTION_EX
@example('fn(b,o,b=0,*a)')                # BUILD_MAP, BUILD_TUPLE, BUILD_TUPLE_UNPACK_WITH_CALL, CALL_FUNCTION_EX
def test_function_call(function_call):
    validate_uncompyle(function_call)


examples = []


@pytest.mark.skip()
@given(function_calls())
def test_generate_hypothesis(function_call):
    examples = set()
    examples.add(function_call)


@pytest.mark.skip()
def test_generate_examples():
    import dis
    example_opcodes = {}
    for example in examples:
        opcodes = tuple(sorted(set(instruction.opname for instruction in dis.Bytecode(example))))
        example_opcodes[opcodes] = example
    for k, v in example_opcodes.items():
        print("@example('" + v + "')   # ", ', '.join(k))
