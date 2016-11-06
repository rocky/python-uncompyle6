import uncompyle6.parser as python_parser
class ParserError(python_parser.ParserError):
    def __init__(self, error, tokens):
        self.error = error # previous exception
        self.tokens = tokens

    def __str__(self):
        lines = ['--- This code section failed: ---']
        lines.extend([str(i) for i in self.tokens])
        lines.extend( ['', str(self.error)] )
        return '\n'.join(lines)
