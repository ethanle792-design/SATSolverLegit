import tarfile
import time

class SATSolverUtils:
    @staticmethod
    def parse_cnf_content(content):
        """Parses a DIMACS CNF string into a clause list and variable count."""
        clauses = []
        num_vars = 0
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(('c', '%')) or line == '0':
                continue
            if line.startswith('p'):
                parts = line.split()
                try:
                    num_vars = int(parts[2])
                except (IndexError, ValueError):
                    pass
                continue
            try:
                lits = [int(x) for x in line.split() if x != '0' and x != '']
                if lits:
                    clauses.append(lits)
            except ValueError:
                continue
        return num_vars, clauses

    @staticmethod
    def process_tar_benchmarks(tar_path, solver_class):
        """Runs the solver against all .cnf files in a .tar.gz archive."""
        sat_count, unsat_count, total_count = 0, 0, 0
        start_time = time.time()
        print(f"\n--- Starting Benchmark: {tar_path} ---")
        
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".cnf")]
                if not members:
                    print("No .cnf files found.")
                    return

                for member in members:
                    total_count += 1
                    f = tar.extractfile(member)
                    content = f.read().decode('utf-8')
                    n_vars, clauses = SATSolverUtils.parse_cnf_content(content)
                    
                    instance_start = time.time()
                    # Initialize and solve
                    solver = solver_class(n_vars, clauses)
                    result = solver.solve()
                    duration = time.time() - instance_start
                    
                    if result == "SATISFIABLE":
                        sat_count += 1
                    else:
                        unsat_count += 1
                    
                    if total_count % 10 == 0 or total_count == len(members):
                        print(f"[{total_count}/{len(members)}] {member.name:30} | {result:12} | {duration:.4f}s")
        except Exception as e:
            print(f"Error during benchmark: {e}")
            return

        total_time = time.time() - start_time
        print(f"\nBENCHMARK COMPLETE")
        print(f"Total: {total_count} | SAT: {sat_count} | UNSAT: {unsat_count}")
        print(f"Total Time: {total_time:.2f}s")
        if total_count > 0:
            print(f"Avg Time:   {total_time/total_count:.4f}s")

    @staticmethod
    def get_minimal_assignments(solutions):
        """
        Analyzes SAT solutions to find common essential variables.
        Works with either a single dictionary or a list of dictionaries.
        """
        # 1. Handle Empty Input
        if not solutions:
            return {}, []

        # 2. Handle Single Solution Input
        # If the input is a dict (one solution), wrap it in a list
        if isinstance(solutions, dict):
            solutions = [solutions]

        # 3. Minimization Logic
        all_vars = solutions[0].keys()
        minimal_set = {}
        
        for var in all_vars:
            # Get every value assigned to this variable across all solutions
            distinct_values = {sol[var] for sol in solutions}
            
            # If the variable has the same value in every solution, it's essential
            if len(distinct_values) == 1:
                minimal_set[var] = list(distinct_values)[0]
                
        return minimal_set, solutions