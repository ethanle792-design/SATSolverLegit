import heapq
import tarfile
import io
import os

# --- PART 1: THE INTELLIGENT HEURISTIC (VSIDS) ---
class VSIDS:
    def __init__(self, num_vars, decay_factor=0.95):
        self.scores = {i: 0.0 for i in range(1, num_vars + 1)}
        self.decay_factor = decay_factor
        self.step = 1.0
        self.heap = [(-0.0, i) for i in range(1, num_vars + 1)]
        heapq.heapify(self.heap)

    def bump_variable(self, var):
        self.scores[var] += self.step
        heapq.heappush(self.heap, (-self.scores[var], var))

    def decay_scores(self):
        self.step /= self.decay_factor

    def pick_variable(self, assignment):
        while self.heap:
            score, var = heapq.heappop(self.heap)
            if -score == self.scores[var] and assignment[var] == 0:
                return var
        return None

# --- PART 2: THE 2-WATCHED LITERAL ENGINE ---
class SATSolver:
    def __init__(self, num_vars, clauses):
        self.num_vars = num_vars
        self.clauses = [list(c) for c in clauses]
        self.assignment = [0] * (num_vars + 1)
        self.trail = []
        self.levels = [0] * (num_vars + 1)
        self.current_level = 0
        self.head = 0  # CRITICAL: Pointer for iterative propagation
        
        self.vsids = VSIDS(num_vars)
        self.watches = {i: [] for i in range(-num_vars, num_vars + 1) if i != 0}
        
        for i, clause in enumerate(self.clauses):
            if len(clause) >= 2:
                self.watches[clause[0]].append(i)
                self.watches[clause[1]].append(i)
            elif len(clause) == 1:
                self.assign(clause[0])

    def get_lit_val(self, lit):
        val = self.assignment[abs(lit)]
        if val == 0: return 0
        return 1 if (lit > 0 and val == 1) or (lit < 0 and val == -1) else -1

    def assign(self, lit):
        var = abs(lit)
        self.assignment[var] = 1 if lit > 0 else -1
        self.trail.append(lit)
        self.levels[var] = self.current_level

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
                        self.assign(clause[0])
                        j += 1
                    elif val0 == -1:
                        return clause
                    else:
                        j += 1
        return None

    def backtrack(self, to_level):
        """Resets the trail and variables back to a specific decision level."""
        while self.trail:
            lit = self.trail[-1]
            var = abs(lit)
            if self.levels[var] <= to_level:
                break
            self.assignment[var] = 0
            self.levels[var] = 0
            self.trail.pop()
        
        # CRITICAL FIX: Reset the propagation head to the end of the new trail
        self.head = len(self.trail)
        self.current_level = to_level

    def solve(self):
        # 1. Initial Propagation (Level 0)
        if self.propagate(): 
            return "UNSATISFIABLE"
        
        while True:
            # 2. Decision
            var = self.vsids.pick_variable(self.assignment)
            if var is None: 
                return "SATISFIABLE"
            
            self.current_level += 1
            decision_lit = var # Standard: Try setting variable to True (Positive ID)
            self.assign(decision_lit)
            
            conflict = self.propagate()
            
            # 3. Conflict Resolution
            while conflict:
                if self.current_level == 0:
                    return "UNSATISFIABLE"
                
                # VSIDS Bump
                for lit in conflict:
                    self.vsids.bump_variable(abs(lit))
                self.vsids.decay_scores()
                
                # Chronological Backtrack: 
                # In this simple version, we backtrack and then flipping 
                # would happen via further search or more complex logic. 
                # For basic correctness, we jump back and the loop continues.
                self.backtrack(self.current_level - 1)
                
                # To ensure it doesn't get stuck, we need to force 
                # the opposite of the failed decision if we want DPLL.
                # However, with VSIDS, we just let it pick again.
                # For a guaranteed UNSAT find, let's use a simpler DPLL-style flip:
                self.assign(-decision_lit)
                conflict = self.propagate()
                
                if conflict:
                    # If both True and False fail, we must go up another level
                    if self.current_level == 0: return "UNSATISFIABLE"
                    self.backtrack(self.current_level - 1)
                    # Loop will re-run 'while conflict'
                    
# --- PART 3: UTILITIES & BENCHMARKING ---
def parse_cnf_content(content):
    clauses = []
    num_vars = 0
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith(('c', '%')) or line == '0': continue
        if line.startswith('p'):
            parts = line.split()
            num_vars = int(parts[2])
            continue
        try:
            lits = [int(x) for x in line.split() if x != '0' and x != '']
            if lits: clauses.append(lits)
        except ValueError: continue
    return num_vars, clauses

import tarfile
import time

def process_tar_benchmarks(tar_path):
    sat_count = 0
    unsat_count = 0
    total_count = 0
    start_time = time.time()
    
    print(f"\n--- Starting Benchmark: {tar_path} ---")
    
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            # Get all .cnf files
            members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".cnf")]
            total_files = len(members)
            
            if total_files == 0:
                print("No .cnf files found in the archive.")
                return

            for member in members:
                total_count += 1
                
                # Extract and parse the file content
                f = tar.extractfile(member)
                content = f.read().decode('utf-8')
                n_vars, clauses = parse_cnf_content(content)
                
                # Solve the instance
                instance_start = time.time()
                solver = SATSolver(n_vars, clauses)
                result = solver.solve()
                instance_end = time.time()
                
                # Track SAT/UNSAT
                if result == "SATISFIABLE":
                    sat_count += 1
                else:
                    unsat_count += 1
                
                # Progress Update every 10 files
                if total_count % 10 == 0 or total_count == total_files:
                    print(f"[{total_count}/{total_files}] {member.name:30} | {result:12} | {instance_end - instance_start:.4f}s")

    except FileNotFoundError:
        print(f"Error: Could not find the file '{tar_path}'")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # Final Summary
    end_time = time.time()
    print("\n" + "="*45)
    print(f"BENCHMARK COMPLETE")
    print("-" * 45)
    print(f"Total Instances:    {total_count}")
    print(f"SATISFIABLE:        {sat_count}")
    print(f"UNSATISFIABLE:      {unsat_count}")
    print(f"Total Time:         {end_time - start_time:.2f} seconds")
    print(f"Average Solve Time: {(end_time - start_time)/total_count:.4f}s" if total_count > 0 else "")
    print("="*45)

# --- Updated Main to use the Tar Processor ---
if __name__ == "__main__":
    # 1. Update this to your actual filename
    MY_TAR_FILE = "uf20-91.tar.gz" 
    
    # 2. Run the processor
    process_tar_benchmarks(MY_TAR_FILE)

