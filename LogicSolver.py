from itertools import combinations, product

class LogicSolver:
    def __init__(self, parser_instance, solver_class):
        self.parser = parser_instance
        self.solver_class = solver_class
        self.var_to_id = {}
        self.id_to_var = {}
        self.next_id = 1

    # used to track the variables names given in the expression
    def _get_var_id(self, name):
        if name not in self.var_to_id:
            self.var_to_id[name] = self.next_id
            self.id_to_var[self.next_id] = name
            self.next_id += 1
        return self.var_to_id[name]
    
    # Our initial function to solve the expression, but it only outputs one solution. 
    def solve_expression(self, expression_string, string_assumptions=None):
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
    
    # Upgraded function to find every solution possible in a given expression.
    def solve_all(self, expression_string, string_assumptions=None):
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

        # loop to continuously find solutions until the solver says it can't be solved. 
        while True:
            solver = self.solver_class(num_vars, working_clauses, pre_assignments=int_assumptions)
            result = solver.solve()

            if result != "SATISFIABLE":
                break

            # save unique solution
            readable = {}
            for i in range(1, num_vars + 1):
                readable[self.id_to_var[i]] = "True" if solver.assignment[i] == 1 else "False"
            all_solutions.append(readable)

            # block said solution to find another unique one. 
            blocking_clause = []
            for i in range(1, num_vars + 1):
                blocking_clause.append(-i if solver.assignment[i] == 1 else i)
            working_clauses.append(blocking_clause)

        return all_solutions
    
    # Given the whole set of solution, it wil find the minimal sets of variables. 
    def get_minimal(self, all_solutions):
        if not all_solutions: #make sure there even is a solution
            return None
        if len(all_solutions) == 1:
            return all_solutions

        all_vars = list(all_solutions[0].keys())
        simplified = []
        seen = set()
        solution_set = [frozenset(s.items()) for s in all_solutions] # make sure the original set doesn't get modified and order doesn't matter for future comparisons

        for sol in all_solutions:
            essential = dict(sol)

            for size in range(1, len(all_vars) + 1):
                found = False
                for subset in combinations(all_vars, size):
                    subset_vals = {v: sol[v] for v in subset}
                    outside_vars = [v for v in all_vars if v not in subset]

                    # find all solutions matching this subset
                    matching = [s for s in all_solutions if all(s[v] == subset_vals[v] for v in subset)]

                    if not matching:
                        continue

                    # outside variables must be 100% free 
                    expected_count = 2 ** len(outside_vars) # for a set of variables to be the minimum, it must be the solution for 2^(number of other variables) combos
                    if len(matching) != expected_count:
                        continue   # outside vars are not fully free

                    # double check all combinations are actually in solutions
                    outside_combos = list(product(['True', 'False'], repeat=len(outside_vars)))
                    all_covered = True
                    for combo in outside_combos:
                        candidate = dict(subset_vals)
                        candidate.update(zip(outside_vars, combo))
                        if frozenset(candidate.items()) not in solution_set:
                            all_covered = False
                            break

                    if all_covered:
                        essential = subset_vals
                        found = True
                        break
                if found:
                    break

            key = tuple(sorted(essential.items()))
            if key not in seen:
                seen.add(key)
                simplified.append(essential)

        return simplified
