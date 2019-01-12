# std
# test
from uncompyle6 import PYTHON_VERSION, deparse_code
import pytest
pytestmark = pytest.mark.skipif(PYTHON_VERSION <= 2.6,
                                reason='hypothesis needs 2.7 or later')
if PYTHON_VERSION > 2.6:

    import hypothesis
    from hypothesis import strategies as st

    # uncompyle6


    @st.composite
    def expressions(draw):
        # todo : would be nice to generate expressions using hypothesis however
        # this is pretty involved so for now just use a corpus of expressions
        # from which to select.
        return draw(st.sampled_from((
            'abc',
            'len(items)',
            'x + 1',
            'lineno',
            'container',
            'self.attribute',
            'self.method()',
            # These expressions are failing, I think these are control
            # flow problems rather than problems with FORMAT_VALUE,
            # however I need to confirm this...
            #'sorted(items, key=lambda x: x.name)',
            #'func(*args, **kwargs)',
            #'text or default',
            #'43 if life_the_universe and everything else None'
        )))


    @st.composite
    def format_specifiers(draw):
        """
        Generate a valid format specifier using the rules:

        format_spec ::=  [[fill]align][sign][#][0][width][,][.precision][type]
        fill        ::=  <any character>
        align       ::=  "<" | ">" | "=" | "^"
        sign        ::=  "+" | "-" | " "
        width       ::=  integer
        precision   ::=  integer
        type        ::=  "b" | "c" | "d" | "e" | "E" | "f" | "F" | "g" | "G" | "n" | "o" | "s" | "x" | "X" | "%"

        See https://docs.python.org/2/library/string.html

        :param draw: Let hypothesis draw from other strategies.

        :return: An example format_specifier.
        """
        alphabet_strategy = st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
        fill = draw(st.one_of(alphabet_strategy, st.none()))
        align = draw(st.sampled_from(list('<>=^')))
        fill_align = (fill + align or '') if fill else ''

        type_ = draw(st.sampled_from('bcdeEfFgGnosxX%'))
        can_have_sign = type_ in 'deEfFgGnoxX%'
        can_have_comma = type_ in 'deEfFgG%'
        can_have_precision = type_ in 'fFgG'
        can_have_pound = type_ in 'boxX%'
        can_have_zero = type_ in 'oxX'

        sign = draw(st.sampled_from(list('+- ') + [''])) if can_have_sign else ''
        pound = draw(st.sampled_from(('#', '',))) if can_have_pound else ''
        zero = draw(st.sampled_from(('0', '',))) if can_have_zero else ''

        int_strategy = st.integers(min_value=1, max_value=1000)

        width = draw(st.one_of(int_strategy, st.none()))
        width = str(width) if width is not None else ''

        comma = draw(st.sampled_from((',', '',))) if can_have_comma else ''
        if can_have_precision:
            precision = draw(st.one_of(int_strategy, st.none()))
            precision = '.' + str(precision) if precision else ''
        else:
            precision = ''

        return ''.join((fill_align, sign, pound, zero, width, comma, precision, type_,))


    @st.composite
    def fstrings(draw):
        """
        Generate a valid f-string.
        See https://www.python.org/dev/peps/pep-0498/#specification

        :param draw: Let hypothsis draw from other strategies.

        :return: A valid f-string.
        """
        character_strategy = st.characters(
            blacklist_characters='\r\n\'\\s{}',
            min_codepoint=1,
            max_codepoint=1000,
        )
        is_raw = draw(st.booleans())
        integer_strategy = st.integers(min_value=0, max_value=3)
        expression_count = draw(integer_strategy)
        content = []
        for _ in range(expression_count):
            expression = draw(expressions())
            conversion = draw(st.sampled_from(('', '!s', '!r', '!a',)))
            has_specifier = draw(st.booleans())
            specifier = ':' + draw(format_specifiers()) if has_specifier else ''
            content.append('{{{}{}}}'.format(expression, conversion, specifier))
            content.append(draw(st.text(character_strategy)))
        content = ''.join(content)
        return "f{}'{}'".format('r' if is_raw else '', content)


    @pytest.mark.skipif(PYTHON_VERSION != 3.6, reason='need Python 3.6')
    @hypothesis.given(format_specifiers())
    def test_format_specifiers(format_specifier):
        """Verify that format_specifiers generates valid specifiers"""
        try:
            exec('"{:' + format_specifier + '}".format(0)')
        except ValueError as e:
            if 'Unknown format code' not in str(e):
                raise


    def run_test(text):
        hypothesis.assume(len(text))
        hypothesis.assume("f'{" in text)
        expr = text + '\n'
        code = compile(expr, '<string>', 'single')
        deparsed = deparse_code(PYTHON_VERSION, code, compile_mode='single')
        recompiled = compile(deparsed.text, '<string>', 'single')
        if recompiled != code:
            assert 'dis(' + deparsed.text.strip('\n') + ')' == 'dis(' + expr.strip('\n') + ')'


    @pytest.mark.skipif(PYTHON_VERSION != 3.6, reason='need Python 3.6')
    @hypothesis.given(fstrings())
    def test_uncompyle_fstring(fstring):
        """Verify uncompyling fstring bytecode"""
        run_test(fstring)


    @pytest.mark.skipif(PYTHON_VERSION < 3.6, reason='need Python 3.6+')
    @pytest.mark.parametrize('fstring', [
        "f'{abc}{abc!s}'",
        "f'{abc}0'",
    ])
    def test_uncompyle_direct(fstring):
        """useful for debugging"""
        run_test(fstring)
