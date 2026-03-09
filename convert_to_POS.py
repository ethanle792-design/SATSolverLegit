keywords = ['AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR', 'XNOR']

# ─────────────────────────────────────────────────────────────
# STEP 1: Tokenizer
# ─────────────────────────────────────────────────────────────

def input_to_arrayterms(input_string: str):
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
            if word.upper() in keywords:
                terms.append(word.upper())
            else:
                terms.append(word)
            i = j
        else:
            raise ValueError(f"Unexpected character '{character}' at position {i}")
    return terms


# ─────────────────────────────────────────────────────────────
# STEP 2: Token list → AST
# Each node is a tuple: ('AND', l, r), ('OR', l, r),
#                       ('NOT', child), ('VAR', name)
# ─────────────────────────────────────────────────────────────

def parse(tokens):
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
            node = parse_and()
            consume()           # ')'
            return node
        elif tok == 'XOR':
            raise ValueError("XOR must be between two operands")
        elif tok not in (None, ')', '.', '+', 'AND', 'OR', 'NOT', '~') and tok not in keywords:
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
                # (a AND ~b) OR (~a AND b)
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
# STEP 3: Push NOTs inward (De Morgan's laws)
# Ensures NOT only sits directly on a variable, never on AND/OR
# ─────────────────────────────────────────────────────────────

def push_not_inward(ast):
    kind = ast[0]

    if kind == 'VAR':
        return ast

    elif kind == 'NOT':
        child = ast[1]

        if child[0] == 'VAR':
            return ast                          # NOT on a variable — already fine

        elif child[0] == 'NOT':
            return push_not_inward(child[1])    # double negation — cancel out

        elif child[0] == 'AND':
            # De Morgan: NOT(a AND b) → (NOT a) OR (NOT b)
            return push_not_inward(('OR',
                                    ('NOT', child[1]),
                                    ('NOT', child[2])))

        elif child[0] == 'OR':
            # De Morgan: NOT(a OR b) → (NOT a) AND (NOT b)
            return push_not_inward(('AND',
                                    ('NOT', child[1]),
                                    ('NOT', child[2])))

    elif kind == 'AND':
        return ('AND', push_not_inward(ast[1]), push_not_inward(ast[2]))

    elif kind == 'OR':
        return ('OR', push_not_inward(ast[1]), push_not_inward(ast[2]))


# ─────────────────────────────────────────────────────────────
# STEP 4: Distribute ORs over ANDs
# Turns OR(AND(a,b), c) into AND(OR(a,c), OR(b,c))
# Repeats until nothing changes (fully distributed)
# ─────────────────────────────────────────────────────────────

def distribute(ast):
    kind = ast[0]

    if kind in ('VAR', 'NOT'):
        return ast

    elif kind == 'AND':
        return ('AND', distribute(ast[1]), distribute(ast[2]))

    elif kind == 'OR':
        left  = distribute(ast[1])
        right = distribute(ast[2])

        # OR(AND(a,b), c)  →  AND(OR(a,c), OR(b,c))
        if left[0] == 'AND':
            return distribute(('AND',
                               ('OR', left[1], right),
                               ('OR', left[2], right)))

        # OR(a, AND(b,c))  →  AND(OR(a,b), OR(a,c))
        elif right[0] == 'AND':
            return distribute(('AND',
                               ('OR', left, right[1]),
                               ('OR', left, right[2])))

        else:
            return ('OR', left, right)


# ─────────────────────────────────────────────────────────────
# STEP 5: AST → 2D clause array
# AND nodes split into separate rows
# OR nodes stay in the same row
# ─────────────────────────────────────────────────────────────

def ast_to_clauses(ast):
    """Flatten a CNF AST into a 2D list of literals."""
    clauses = []

    def collect_clause(node, current_clause):
        """Walk an OR-tree and collect all literals into one clause."""
        if node[0] == 'VAR':
            current_clause.append(node[1])
        elif node[0] == 'NOT':
            current_clause.append('~' + node[1][1])   # NOT VAR → '~varname'
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
# MAIN: tie all steps together
# ─────────────────────────────────────────────────────────────

def to_pos(input_string: str):
    """
    Convert any Boolean expression string into a 2D POS/CNF clause array.
    Each row is a clause (list of literals) that must contain at least one True literal.
    """
    print(f"\nInput: {input_string}")

    tokens = input_to_arrayterms(input_string)
    print(f"Tokens:      {tokens}")

    ast = parse(tokens)
    print(f"AST:         {ast}")

    ast = push_not_inward(ast)
    print(f"NOTs pushed: {ast}")

    ast = distribute(ast)
    print(f"Distributed: {ast}")

    clauses = ast_to_clauses(ast)
    print(f"POS clauses: {clauses}")
    return clauses


# ─────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────

to_pos("(~x1 + x2) . (x3 + ~x4) . x1")         # already CNF
to_pos("~x1 XOR x2")                             # XOR with negated var
to_pos("(~x1 AND x2) XOR (x3 OR x4)")            # grouped XOR
to_pos("~(x1 AND x2)")                           # De Morgan
to_pos("(x1 AND x2) OR (x3 AND x4)")             # needs distribution