class LogicSolver:
    def __init__(self, parser_instance, solver_class):
        self.parser = parser_instance
        self.solver_class = solver_class
        self.var_to_id = {}
        self.id_to_var = {}
        self.next_id = 1

    def _get_var_id(self, name):
        """Internal: Manages the 'phonebook' of variable names to IDs."""
        if name not in self.var_to_id:
            self.var_to_id[name] = self.next_id
            self.id_to_var[self.next_id] = name
            self.next_id += 1
        return self.var_to_id[name]
    
    
    def solve_expression(self, expression_string, string_assumptions=None):
        """
        Takes a boolean string and optional assumptions.
        Returns (Result, ReadableAssignment).
        """
        # 1. Parse string to POS list of strings
        string_clauses = self.parser.to_pos(expression_string)
        
        # 2. Map strings to integers
        int_clauses = []
        for clause in string_clauses:
            int_clause = []
            for lit in clause:
                is_neg = lit.startswith('~')
                name = lit.lstrip('~')
                var_id = self._get_var_id(name)
                int_clause.append(-var_id if is_neg else var_id)
            int_clauses.append(int_clause)

        # 3. Map string assumptions to integer IDs
        int_assumptions = {}
        if string_assumptions:
            for name, val in string_assumptions.items():
                if name in self.var_to_id:
                    int_assumptions[self.var_to_id[name]] = val

        # 4. Run Engine
        num_vars = self.next_id - 1
        solver = self.solver_class(num_vars, int_clauses, pre_assignments=int_assumptions)
        result = solver.solve()

        # 5. Reverse map result to readable format
        readable_assignment = {}
        if result == "SATISFIABLE":
            for i in range(1, num_vars + 1):
                var_name = self.id_to_var[i]
                val = solver.assignment[i]
                readable_assignment[var_name] = "True" if val == 1 else "False"

        return result, readable_assignment
    
    def solve_all(self, expression_string, string_assumptions=None):
        """
        Returns a list of ALL satisfying assignments.
        Each entry is a readable dict e.g. {'x1': 'True', 'x2': 'False'}
        Returns an empty list if UNSAT.
        """
        # Steps 1-3 are identical to solve_expression
        string_clauses = self.parser.to_pos(expression_string)

        int_clauses = []
        for clause in string_clauses:
            int_clause = []
            for lit in clause:
                is_neg = lit.startswith('~')
                name = lit.lstrip('~')
                var_id = self._get_var_id(name)
                int_clause.append(-var_id if is_neg else var_id)
            int_clauses.append(int_clause)

        int_assumptions = {}
        if string_assumptions:
            for name, val in string_assumptions.items():
                if name in self.var_to_id:
                    int_assumptions[self.var_to_id[name]] = val

        num_vars = self.next_id - 1

        # take a copy so blocking clauses don't affect the original
        working_clauses = [clause[:] for clause in int_clauses]
        all_solutions = []

        while True:
            solver = self.solver_class(num_vars, working_clauses, pre_assignments=int_assumptions)
            result = solver.solve()

            if result != "SATISFIABLE":
                break

            # save readable solution
            readable = {}
            for i in range(1, num_vars + 1):
                readable[self.id_to_var[i]] = "True" if solver.assignment[i] == 1 else "False"
            all_solutions.append(readable)

            # block this solution so next run finds a different one
            blocking_clause = []
            for i in range(1, num_vars + 1):
                blocking_clause.append(-i if solver.assignment[i] == 1 else i)
            working_clauses.append(blocking_clause)

        return all_solutions
