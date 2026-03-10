class BooleanLogicParser:
    def __init__(self):
        self.keywords = ['AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR', 'XNOR']

    # Take a string and turn it into a list of usable terms. 
    def input_to_arrayterms(self, input_string: str):
        terms = []
        i = 0
        while i < len(input_string):
            character = input_string[i]
            if character == ' ': # skip space
                i += 1
            elif character in ['+', '(', ')', '~', '.']: # append operator symbols
                terms.append(character)
                i += 1
            elif character.isalnum() or character == '_': # append variables and keywords
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

    # Make the list of terms into an abstract tree similar to a binary tree, but use operators as nodes
    def parse(self, tokens):
        pos = [0]   

    #Below are helper functions for recursive parsing to get the POS boolean form. 
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
            return parse_var_or_group()

        def parse_var_or_group():
            tok = peek()
            if tok == '(':
                consume()           # '('
                node = parse_expression()
                consume()           # ')'
                return node
            elif tok == 'XOR':
                raise ValueError("XOR must be between two operands")
            elif tok not in (None, ')', '.', '+', 'AND', 'OR', 'NOT', '~') and tok not in self.keywords:
                consume()
                return ('VAR', tok)
            else:
                raise SyntaxError(f"Unexpected token: {tok!r}")

        def parse_expression():
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

        abstract_tree = parse_expression()
        if pos[0] != len(tokens):
            raise SyntaxError(f"Unexpected token at position {pos[0]}: {tokens[pos[0]]!r}")
        return abstract_tree

    # Helper function to apply Demorgan's law into a group of variables. 
    def push_not_inward(self, abstract_tree):
        kind = abstract_tree[0]
        if kind == 'VAR':
            return abstract_tree
        elif kind == 'NOT':
            child = abstract_tree[1]
            if child[0] == 'VAR':
                return abstract_tree
            elif child[0] == 'NOT':
                return self.push_not_inward(child[1])
            elif child[0] == 'AND':
                return self.push_not_inward(('OR', ('NOT', child[1]), ('NOT', child[2])))
            elif child[0] == 'OR':
                return self.push_not_inward(('AND', ('NOT', child[1]), ('NOT', child[2])))
        elif kind == 'AND':
            return ('AND', self.push_not_inward(abstract_tree[1]), self.push_not_inward(abstract_tree[2]))
        elif kind == 'OR':
            return ('OR', self.push_not_inward(abstract_tree[1]), self.push_not_inward(abstract_tree[2]))

    # helper function to distribute OR over AND to get the final POS form.
    def distribute(self, abstract_tree):
        kind = abstract_tree[0]
        if kind in ('VAR', 'NOT'):
            return abstract_tree
        elif kind == 'AND':
            return ('AND', self.distribute(abstract_tree[1]), self.distribute(abstract_tree[2]))
        elif kind == 'OR':
            left  = self.distribute(abstract_tree[1])
            right = self.distribute(abstract_tree[2])
            if left[0] == 'AND':
                return self.distribute(('AND', ('OR', left[1], right), ('OR', left[2], right)))
            elif right[0] == 'AND':
                return self.distribute(('AND', ('OR', left, right[1]), ('OR', left, right[2])))
            else:
                return ('OR', left, right)

    # Change the abstract tree into a list for easy SAT finding.
    def abstract_tree_to_clauses(self, abstract_tree):
        """Flatten a CNF abstract_tree into a 2D list of literals."""
        clauses = []

        def collect_clause(node, current_clause):
            if node[0] == 'VAR':
                current_clause.append(node[1])
            elif node[0] == 'NOT':
                current_clause.append('~' + node[1][1])
            elif node[0] == 'OR':
                collect_clause(node[1], current_clause)
                collect_clause(node[2], current_clause)

        def split(node):
            if node[0] == 'AND':
                split(node[1])
                split(node[2])
            else:
                clause = []
                collect_clause(node, clause)
                clauses.append(clause)

        split(abstract_tree)
        return clauses

    # what to call to get the final POS form. 
    def to_pos(self, input_string: str, verbose=False):
        if verbose: print(f"\nProcessing: {input_string}")
        
        tokens = self.input_to_arrayterms(input_string)
        abstract_tree = self.parse(tokens)
        abstract_tree = self.push_not_inward(abstract_tree)
        abstract_tree = self.distribute(abstract_tree)
        clauses = self.abstract_tree_to_clauses(abstract_tree)
        
        return clauses