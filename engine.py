from heuristics import VSIDS

class SATSolver:
    def __init__(self, num_vars, clauses):
        self.num_vars = num_vars
        self.clauses = [list(c) for c in clauses]
        self.assignment = [0] * (num_vars + 1)
        self.trail = []
        self.levels = [0] * (num_vars + 1)
        self.decision_stack = [] 
        self.current_level = 0
        self.head = 0  
        self.ok = True
        
        self.vsids = VSIDS(num_vars)
        self.watches = {i: [] for i in range(-num_vars, num_vars + 1) if i != 0}
        
        for i, clause in enumerate(self.clauses):
            if len(clause) >= 2:
                self.watches[clause[0]].append(i)
                self.watches[clause[1]].append(i)
            elif len(clause) == 1:
                if not self.assign(clause[0], 0):
                    self.ok = False

    def get_lit_val(self, lit):
        val = self.assignment[abs(lit)]
        if val == 0: return 0
        return 1 if (lit > 0 and val == 1) or (lit < 0 and val == -1) else -1

    def assign(self, lit, level):
        var = abs(lit)
        if self.assignment[var] != 0:
            return self.assignment[var] == (1 if lit > 0 else -1)
        self.assignment[var] = 1 if lit > 0 else -1
        self.trail.append(lit)
        self.levels[var] = level
        return True

    def propagate(self):
        while self.head < len(self.trail):
            last_lit = self.trail[self.head]
            self.head += 1
            false_lit = -last_lit
            if false_lit not in self.watches: continue
            
            watch_list = self.watches[false_lit]
            j = 0
            while j < len(watch_list):
                idx = watch_list[j]
                clause = self.clauses[idx]
                if clause[0] == false_lit:
                    clause[0], clause[1] = clause[1], clause[0]
                if self.get_lit_val(clause[0]) == 1:
                    j += 1
                    continue
                found = False
                for k in range(2, len(clause)):
                    if self.get_lit_val(clause[k]) != -1:
                        new_watch = clause[k]
                        clause[1], clause[k] = clause[k], clause[1]
                        self.watches[new_watch].append(idx)
                        watch_list[j] = watch_list[-1]
                        watch_list.pop()
                        found = True
                        break
                if not found:
                    val0 = self.get_lit_val(clause[0])
                    if val0 == 0:
                        self.assign(clause[0], self.current_level)
                        j += 1
                    elif val0 == -1: return clause
                    else: j += 1
        return None

    def backtrack(self, to_level):
        while self.trail:
            lit = self.trail[-1]
            var = abs(lit)
            if self.levels[var] <= to_level: break
            self.assignment[var] = 0
            self.levels[var] = 0
            self.trail.pop()
        self.head = len(self.trail)
        self.current_level = to_level
        self.decision_stack = self.decision_stack[:to_level]

    def solve(self):
        if not self.ok: return "UNSATISFIABLE"
        while True:
            conflict = self.propagate()
            if conflict:
                if self.current_level == 0: return "UNSATISFIABLE"
                for lit in conflict:
                    self.vsids.bump_variable(abs(lit))
                self.vsids.decay_scores()
                last_decision = self.decision_stack.pop()
                self.backtrack(self.current_level - 1)
                self.assign(-last_decision, self.current_level)
                continue
            var, phase = self.vsids.pick_variable(self.assignment)
            if var is None: return "SATISFIABLE"
            self.current_level += 1
            decision_lit = var if phase == 1 else -var
            self.decision_stack.append(decision_lit)
            self.assign(decision_lit, self.current_level)