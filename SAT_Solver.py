class BooleanLogicParser:
    def __init__(self):
        self.keywords = ['AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR', 'XNOR']

    # ─────────────────────────────────────────────────────────────
    # STEP 1: Tokenizer
    # ─────────────────────────────────────────────────────────────
    def input_to_arrayterms(self, input_string: str):
        terms = []
        i = 0
        while i < len(input_string):
            character = input_string[i]
            if character == ' ':
                i += 1
            elif character in ['+', '(', ')', '~', '.']:
                terms.append(character)
                i += 1
            elif character.isalnum() or character == '_':
                j = i
                while j < len(input_string) and (input_string[j].isalnum() or input_string[j] == '_'):
                    j += 1
                word = input_string[i:j]
                if word.upper() in self.keywords:
                    terms.append(word.upper())
                else:
                    terms.append(word)
                i = j
            else:
                raise ValueError(f"Unexpected character '{character}' at position {i}")
        return terms

    # ─────────────────────────────────────────────────────────────
    # STEP 2: Token list → AST
    # ─────────────────────────────────────────────────────────────
    def parse(self, tokens):
        """Turn a flat token list into a nested AST."""
        pos = [0]   # use a list so inner functions can modify it

        def peek():
            return tokens[pos[0]] if pos[0] < len(tokens) else None

        def consume():
            tok = tokens[pos[0]]
            pos[0] += 1
            return tok

        def parse_and():
            node = parse_or()
            while peek() in ('.', 'AND'):
                consume()
                right = parse_or()
                node = ('AND', node, right)
            return node

        def parse_or():
            node = parse_not()
            while peek() in ('+', 'OR'):
                consume()
                right = parse_not()
                node = ('OR', node, right)
            return node

        def parse_not():
            if peek() in ('~', 'NOT'):
                consume()
                child = parse_not()
                return ('NOT', child)
            return parse_atom()

        def parse_atom():
            tok = peek()
            if tok == '(':
                consume()           # '('
                node = parse_expr()
                consume()           # ')'
                return node
            elif tok == 'XOR':
                raise ValueError("XOR must be between two operands")
            elif tok not in (None, ')', '.', '+', 'AND', 'OR', 'NOT', '~') and tok not in self.keywords:
                consume()
                return ('VAR', tok)
            else:
                raise SyntaxError(f"Unexpected token: {tok!r}")

        def parse_expr():
            """Top level — also handles infix XOR/NAND/NOR/XNOR."""
            node = parse_and()
            while peek() in ('XOR', 'NAND', 'NOR', 'XNOR'):
                op = consume()
                right = parse_and()
                if op == 'XOR':
                    node = ('OR',
                            ('AND', node, ('NOT', right)),
                            ('AND', ('NOT', node), right))
                elif op == 'NAND':
                    node = ('NOT', ('AND', node, right))
                elif op == 'NOR':
                    node = ('NOT', ('OR', node, right))
                elif op == 'XNOR':
                    node = ('OR',
                            ('AND', node, right),
                            ('AND', ('NOT', node), ('NOT', right)))
            return node

        ast = parse_expr()
        if pos[0] != len(tokens):
            raise SyntaxError(f"Unexpected token at position {pos[0]}: {tokens[pos[0]]!r}")
        return ast

    # ─────────────────────────────────────────────────────────────
    # STEP 3: Push NOTs inward
    # ─────────────────────────────────────────────────────────────
    def push_not_inward(self, ast):
        kind = ast[0]
        if kind == 'VAR':
            return ast
        elif kind == 'NOT':
            child = ast[1]
            if child[0] == 'VAR':
                return ast
            elif child[0] == 'NOT':
                return self.push_not_inward(child[1])
            elif child[0] == 'AND':
                return self.push_not_inward(('OR', ('NOT', child[1]), ('NOT', child[2])))
            elif child[0] == 'OR':
                return self.push_not_inward(('AND', ('NOT', child[1]), ('NOT', child[2])))
        elif kind == 'AND':
            return ('AND', self.push_not_inward(ast[1]), self.push_not_inward(ast[2]))
        elif kind == 'OR':
            return ('OR', self.push_not_inward(ast[1]), self.push_not_inward(ast[2]))

    # ─────────────────────────────────────────────────────────────
    # STEP 4: Distribute ORs over ANDs
    # ─────────────────────────────────────────────────────────────
    def distribute(self, ast):
        kind = ast[0]
        if kind in ('VAR', 'NOT'):
            return ast
        elif kind == 'AND':
            return ('AND', self.distribute(ast[1]), self.distribute(ast[2]))
        elif kind == 'OR':
            left  = self.distribute(ast[1])
            right = self.distribute(ast[2])
            if left[0] == 'AND':
                return self.distribute(('AND', ('OR', left[1], right), ('OR', left[2], right)))
            elif right[0] == 'AND':
                return self.distribute(('AND', ('OR', left, right[1]), ('OR', left, right[2])))
            else:
                return ('OR', left, right)

    # ─────────────────────────────────────────────────────────────
    # STEP 5: AST → 2D clause array
    # ─────────────────────────────────────────────────────────────
    def ast_to_clauses(self, ast):
        """Flatten a CNF AST into a 2D list of literals."""
        clauses = []

        def collect_clause(node, current_clause):
            if node[0] == 'VAR':
                current_clause.append(node[1])
            elif node[0] == 'NOT':
                current_clause.append('~' + node[1][1])
            elif node[0] == 'OR':
                collect_clause(node[1], current_clause)
                collect_clause(node[2], current_clause)

        def walk(node):
            if node[0] == 'AND':
                walk(node[1])
                walk(node[2])
            else:
                clause = []
                collect_clause(node, clause)
                clauses.append(clause)

        walk(ast)
        return clauses

    # ─────────────────────────────────────────────────────────────
    # MAIN Execution Logic
    # ─────────────────────────────────────────────────────────────
    def to_pos(self, input_string: str, verbose=False):
        if verbose: print(f"\nProcessing: {input_string}")
        
        tokens = self.input_to_arrayterms(input_string)
        ast = self.parse(tokens)
        ast = self.push_not_inward(ast)
        ast = self.distribute(ast)
        clauses = self.ast_to_clauses(ast)
        
        return clauses