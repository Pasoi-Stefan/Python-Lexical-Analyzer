import re


class LexicalError(Exception):
    pass


class Tokenizer:
    @staticmethod
    def new_token_regex(regex):
        newline = r'\n'
        return f'^({regex})$(?!{newline})'

    @staticmethod
    def define_tokens():
        letter = '[a-zA-Z]'
        digit = '[0-9]'
        non_zero_digit = '[1-9]'
        newline = r'\n'
        dot = '\.'

        # diferite variante pentru string (pe o singura linie si pe mai multe linii)
        str_single_quotes = f"'[^'{newline}]*'?"
        str_double_quotes = f'"[^"{newline}]*"?'
        str_three_single_quotes = f"'''((?!''').|{newline})*(''')?"
        str_three_double_quotes = f'"""((?!""").|{newline})*(""")?'

        # https://docs.python.org/3/reference/lexical_analysis.html#keywords
        Tokenizer.keywords = ['False', 'await', 'else', 'import', 'pass', 'None',
                              'break', 'except', 'in', 'raise', 'True', 'class',
                              'finally', 'is', 'return', 'and', 'continue', 'for',
                              'lambda', 'try', 'as', 'def', 'from', 'nonlocal',
                              'while', 'assert', 'del', 'global', 'not', 'with',
                              'async', 'elif', 'if', 'or', 'yield']

        # https://docs.python.org/3/reference/lexical_analysis.html#operators
        Tokenizer.operators = ['+', '-', '*', '**', '/', '//', '%', '@', '<<', '>>', '&',
                               '|', '^', '~', ':=', '<', '>', '<=', '>=', '==', '!=']

        # https://docs.python.org/3/reference/lexical_analysis.html#delimiters
        Tokenizer.delimiters = ['(', ')', '[', ']', '{', '}', ',', ':', '.', ';', '@', '=',
                                '->', '+=', '-=', '*=', '/=', '//=', '%=', '@=', '&=', '|=',
                                '^=', '>>=', '<<=', '**=']

        Tokenizer.identifier = Tokenizer.new_token_regex(f'({letter}|_)({letter}|{digit}|_)*')
        Tokenizer.integer = Tokenizer.new_token_regex(f'{non_zero_digit}{digit}*|0')
        Tokenizer.floating = Tokenizer.new_token_regex(f'({digit}+|(?={dot}{digit})){dot}({digit}+|(?<={digit}{dot}))')
        Tokenizer.string = Tokenizer.new_token_regex(f'{str_single_quotes}|{str_double_quotes}|'
                                                     f'{str_three_single_quotes}|{str_three_double_quotes}')
        Tokenizer.comment = Tokenizer.new_token_regex(f'#[^{newline}]*')

    def __init__(self, file_handler):
        self.file_handler = file_handler
        self.line_num = 1
        self.col_num = 1
        self.start_line_num = 1
        self.start_col_num = 1
        self.token_buffer = ''

    def increment_pointer(self):
        ch = self.file_handler.read(1)

        if ch == '\n':
            self.line_num += 1
            self.col_num = 1
        else:
            self.col_num += 1

    def get_next_character(self):
        curr_offset = self.file_handler.tell()
        ch = self.file_handler.read(1)
        self.file_handler.seek(curr_offset)
        return ch

    def get_next_token(self):
        # initializam pozitia la care a inceput analizarea caracterelor
        self.start_line_num = self.line_num
        self.start_col_num = self.col_num
        # initializam token-ul si tipul acestuia
        token = ''
        token_name = ''
        while True:
            ch = self.get_next_character()
            # print(f'Reading: {repr(ch)}')

            # verificam daca am ajuns la sfarsitul fisierului
            if not ch:
                if token_name == 'INCOMPLETE STRING':
                    raise LexicalError('Incomplete string reached EOF')
                return token, token_name

            self.token_buffer += ch

            # pentru regex-ul fiecarui token il comparam cu caracterele citite in buffer
            # si, daca se potrivesc citim mai departe caracterele, altfel verificam daca avem
            # eroare lexicala
            if self.token_buffer in Tokenizer.keywords:
                token = self.token_buffer
                token_name = 'KEYWORD'
                self.increment_pointer()
                continue

            if re.search(Tokenizer.identifier, self.token_buffer):
                token = self.token_buffer
                token_name = 'IDENTIFIER'
                self.increment_pointer()
                continue

            if re.search(Tokenizer.integer, self.token_buffer):
                token = self.token_buffer
                token_name = 'INTEGER'
                self.increment_pointer()
                continue

            if re.search(Tokenizer.floating, self.token_buffer):
                token = self.token_buffer
                token_name = 'FLOATING'
                self.increment_pointer()
                continue

            # in acest caz, regex-ul se potriveste atat pentru inceput de string cat si pentru string intreg
            if re.search(Tokenizer.string, self.token_buffer):
                if len(self.token_buffer) >= 2 and self.token_buffer.startswith("'") and self.token_buffer.endswith("'") or \
                   len(self.token_buffer) >= 2 and self.token_buffer.startswith('"') and self.token_buffer.endswith('"') or \
                   len(self.token_buffer) >= 6 and self.token_buffer.startswith("'''") and self.token_buffer.endswith("'''") or \
                   len(self.token_buffer) >= 6 and self.token_buffer.startswith('"""') and self.token_buffer.endswith('"""'):
                    token = self.token_buffer
                    token_name = 'STRING'
                    self.increment_pointer()
                    continue
                else:
                    token = self.token_buffer
                    token_name = 'INCOMPLETE STRING'
                    self.increment_pointer()
                    continue

            if re.search(Tokenizer.comment, self.token_buffer):
                token = self.token_buffer
                token_name = 'COMMENT'
                self.increment_pointer()
                continue

            if self.token_buffer in Tokenizer.operators:
                token = self.token_buffer
                token_name = 'OPERATOR'
                self.increment_pointer()
                continue

            if self.token_buffer in Tokenizer.delimiters:
                token = self.token_buffer
                token_name = 'DELIMITER'
                self.increment_pointer()
                continue

            # verificam daca avem eroare lexicala
            if token_name == 'INTEGER':
                if re.search('[a-zA-Z]', ch):
                    raise LexicalError('Invalid integer')

            if token_name == 'FLOATING':
                if re.search('[a-zA-Z]', ch):
                    raise LexicalError('Invalid floating point number')

            if token_name == 'INCOMPLETE STRING':
                if ch == '\n':
                    raise LexicalError('Incomplete string reached end-of-line')

            # daca nu este eroare lexicala, atunci returnam token-ul format pana acum, fara
            # sa consumam caracterul curent
            self.token_buffer = ''
            return token, token_name


if __name__ == '__main__':
    # initializam tokenii in clasa Tokenizer
    Tokenizer.define_tokens()

    with open('example.py') as file_handler:
        t = Tokenizer(file_handler)

        # afisam toti tokenii, inclusiv erorile lexicale, pana la sfarsitul fisierului
        while True:
            try:
                # cat timp avem spatii albe, le ignoram
                while re.search('\s', t.get_next_character()):
                    t.increment_pointer()

                ch = t.get_next_character()

                # verificam daca am ajuns la sfarsitul fisierului
                if not ch:
                    break

                token, token_name = t.get_next_token()

                # afisam tokenii
                print(f'<Type={token_name}, <{token}>, Length={len(token)}, '
                      f'Line={t.start_line_num}, Column={t.start_col_num}>')
            except LexicalError as e:
                # afisam eroarea lexicala
                print(f'Lexical error: {e} - Line: {t.start_line_num} - Column: {t.start_col_num}')
                t.token_buffer = ''

                # ignoram caracterele pana ajungem la spatiile albe
                while re.search('\S', t.get_next_character()):
                    t.increment_pointer()
