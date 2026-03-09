keywords = ['AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR', 'XNOR']

# This function takes an input string and converts it into an array of terms.
def input_to_arrayterms(input_string: str):
    terms = []
    i = 0
    while i < len(input_string):
        character = input_string[i]
        if character == ' ':
            i += 1
        elif character in ['+', '-', '*', '/', '(', ')', '~', '.']:
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
            
print("initial array of terms: " + str(input_to_arrayterms("(~x1 XOR x2)")))

# This function takes the array of terms and extracts the variables, ignoring keywords and operators.
def define_variables(terms):
    variables = []
    for term in terms:
        if term.isalnum() and term.upper() not in keywords:
            variables.append(term)
    return variables

print("defined variables: " + str(define_variables(input_to_arrayterms("(~x1 XOR x2)"))))

# This function takes the array of terms and expands any XOR, NAND, NOR, XNOR operators into their equivalent AND/OR/NOT expressions.
def pop_operand(result):
    """
    Pop the last operand from result.
    If it ends with ')' grab everything back to the matching '('.
    If it ends with a variable (with optional ~) grab just that.
    """
    if not result:
        raise ValueError("Expected an operand but found nothing")

    if result[-1] == ')':
        # find the matching opening parenthesis
        result.pop() 
        group = [')']
        depth = 1
        while result and depth > 0:
            token = result.pop()
            group.insert(0, token)
            if token == ')':
                depth += 1
            elif token == '(':
                depth -= 1
        group.insert(0, '(')  # add back the opening '('
        return group          # returns a list of tokens e.g. ['(', '~x1', 'AND', 'x2', ')']

    else:
        # single variable, check for leading ~
        var = result.pop()
        if result and result[-1] == '~':
            result.pop()
            return ['~' + var]
        return [var]


def get_right_operand(tokens, i):
    """
    Read the next operand from tokens starting at position i.
    Handles: ~x1,  x1,  (~x1 AND x2),  ~(x1 AND x2)
    Returns (operand_as_token_list, new_i)
    """
    # skip spaces if any
    while i < len(tokens) and tokens[i] == ' ':
        i += 1

    if i >= len(tokens):
        raise ValueError("Expected right operand but reached end of input")

    negate_group = False
    if tokens[i] == '~':
        negate_group = True
        i += 1

    if tokens[i] == '(':
        # collect everything up to the matching ')'
        group = ['(']
        i += 1
        depth = 1
        while i < len(tokens) and depth > 0:
            t = tokens[i]
            group.append(t)
            if t == '(':
                depth += 1
            elif t == ')':
                depth -= 1
            i += 1
        if negate_group:
            return ['~('] + group[1:]   # mark as negated group
        return group, i

    else:
        # single variable with optional ~
        var = tokens[i]
        i += 1
        if negate_group:
            return ['~' + var], i
        return [var], i
    
def negate(literal):
    """Flip the ~ on a single literal. ~x1 -> x1,  x1 -> ~x1"""
    if literal.startswith('~'):
        return literal[1:]
    return '~' + literal


def negate_group(operand_tokens):
    """
    Negate an entire operand (single literal or grouped expression).
    Single literal:  ['x1']     -> ['~x1']
    Group:           ['(','x1','AND','x2',')']  -> ['NOT','(','x1','AND','x2',')']
    """
    if len(operand_tokens) == 1:
        return [negate(operand_tokens[0])]
    else:
        return ['NOT'] + operand_tokens

# This function takes the array of terms and expands any XOR, NAND, NOR, XNOR operators into their equivalent AND/OR/NOT expressions.
def expand_operators(tokens):
    result = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if token in ('XOR', 'NOR', 'NAND', 'XNOR'):

            a_tokens = pop_operand(result)

            i += 1
            b_tokens, i = get_right_operand(tokens, i)

            na = negate_group(a_tokens)
            nb = negate_group(b_tokens)

            if token == 'XOR':
                # (a AND ~b) OR (~a AND b)
                result += (
                    ['('] + a_tokens + ['AND'] + nb + [')'] +
                    ['OR'] +
                    ['('] + na + ['AND'] + b_tokens + [')']
                )

            elif token == 'NOR':
                # ~a AND ~b
                result += na + ['AND'] + nb

            elif token == 'NAND':
                # ~a OR ~b
                result += ['('] + na + ['OR'] + nb + [')']

            elif token == 'XNOR':
                # (a AND b) OR (~a AND ~b)
                result += (
                    ['('] + a_tokens + ['AND'] + b_tokens + [')'] +
                    ['OR'] +
                    ['('] + na + ['AND'] + nb + [')']
                )

        else:
            result.append(token)
            i += 1

    return result

# simple variable
print(expand_operators(['x1', 'XOR', 'x2']))
# ['(', 'x1', 'AND', '~x2', ')', 'OR', '(', '~x1', 'AND', 'x2', ')']

# negated variable
print(expand_operators(['~x1', 'XOR', 'x2']))
# ['(', '~x1', 'AND', '~x2', ')', 'OR', '(', 'x1', 'AND', 'x2', ')']

# grouped expression
print(expand_operators(['(', '~x1', 'AND', 'x2', ')', 'XOR', '(', 'x3', 'OR', 'x4', ')']))
