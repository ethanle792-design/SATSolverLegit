import tarfile
import time
from engine import SATSolver
from convert_to_POS import BooleanLogicParser

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

def process_tar_benchmarks(tar_path):
    sat_count, unsat_count, total_count = 0, 0, 0
    start_time = time.time()
    print(f"\n--- Starting Benchmark: {tar_path} ---")
    
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(".cnf")]
            if not members: return print("No .cnf files found.")

            for member in members:
                total_count += 1
                f = tar.extractfile(member)
                content = f.read().decode('utf-8')
                n_vars, clauses = parse_cnf_content(content)
                
                instance_start = time.time()
                solver = SATSolver(n_vars, clauses)
                result = solver.solve()
                duration = time.time() - instance_start
                
                if result == "SATISFIABLE": sat_count += 1
                else: unsat_count += 1
                
                if total_count % 10 == 0 or total_count == len(members):
                    print(f"[{total_count}/{len(members)}] {member.name:30} | {result:12} | {duration:.4f}s")
    except Exception as e:
        return print(f"Error: {e}")

    print(f"\nBENCHMARK COMPLETE\nTotal: {total_count} | SAT: {sat_count} | UNSAT: {unsat_count}")
    print(f"Total Time: {time.time() - start_time:.2f}s")

if __name__ == "__main__":

    # Assuming your SATSolver is in engine.py
    # from engine import SATSolver 

    parser = BooleanLogicParser()

    # 1. Get POS clauses from your boolean string
    # Input: "(x1 AND x2) OR (x3 AND x4)"
    # Output: [['x1', 'x3'], ['x1', 'x4'], ['x2', 'x3'], ['x2', 'x4']]
    my_string = "(~x1 OR x2) AND (x3 or ~x4) AND x1"
    string_clauses = parser.to_pos(my_string)
    print(f"Parsed String Clauses: {string_clauses}")

    # 2. Map variable names (x1, x2...) to unique integers (1, 2...)
    var_to_id = {}
    id_to_var = {}
    next_id = 1
    int_clauses = []

    for clause in string_clauses:
        int_clause = []
        for lit in clause:
            is_neg = lit.startswith('~')
            name = lit.lstrip('~')
            
            if name not in var_to_id:
                var_to_id[name] = next_id
                id_to_var[next_id] = name
                next_id += 1
            
            var_id = var_to_id[name]
            int_clause.append(-var_id if is_neg else var_id)
        int_clauses.append(int_clause)

    num_vars = len(var_to_id)

    # 3. Set Assumptions using the 'x1' format
    # Example: Force x1 to be True and x3 to be False
    #my_string_assumptions = {"x1": -1}
    my_string_assumptions = {}
    
    # Map these string names to their integer IDs for the solver
    int_assumptions = {}
    for name, val in my_string_assumptions.items():
        if name in var_to_id:
            int_assumptions[var_to_id[name]] = val

    # 4. Initialize and Run the Solver
    solver = SATSolver(num_vars, int_clauses, pre_assignments=int_assumptions)
    result = solver.solve()

    # 5. Output the results in the 'x1' format
    print(f"\nResult with assumptions {my_string_assumptions}: {result}")
    if result == "SATISFIABLE":
        readable_assignment = {}
        for i in range(1, num_vars + 1):
            var_name = id_to_var[i]
            val = solver.assignment[i]
            readable_assignment[var_name] = "True" if val == 1 else "False"
        
        print(f"Mapped Solution: {readable_assignment}")










 
    # # Example CNF Data
    # num_vars = 10
    # clauses = [[1, 2], [-1, 3], [4, 5]]

    # # The new feature: forcing specific variables
    # # Format: {variable_index: value} where value is 1 (True) or -1 (False)
    # my_assumptions = {1: 1, 5: -1} 

    # solver = SATSolver(num_vars, clauses, pre_assignments=my_assumptions)
    # result = solver.solve()

    # print(f"Result with assumptions {my_assumptions}: {result}")
    # if result == "SATISFIABLE":
    #     print(f"Full Assignment: {solver.assignment[1:]}")
    # process_tar_benchmarks("uf20-91.tar.gz")
    
