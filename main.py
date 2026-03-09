import tarfile
import time
from engine import SATSolver
from convert_to_POS import BooleanLogicParser
from LogicSolver import LogicSolver

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

    # Initialize components
    parser = BooleanLogicParser()
    logic_wrapper = LogicSolver(parser, SATSolver)

    # Define your problem
    my_string = "(~x1 OR x2) AND (x3 or ~x4) AND x1"
    my_assumptions = {} # e.g., {"x2": -1} to force x2 False

    # ── CHANGED: solve_all instead of solve_expression ──
    all_solutions = logic_wrapper.solve_all(my_string, my_assumptions)

    # Output
    print(f"Expression: {my_string}")
    print(f"Assumptions: {my_assumptions}")

    if not all_solutions:
        print("Status:      UNSAT — no satisfying assignment exists.")
    else:
        print(f"Status:      SATISFIABLE — {len(all_solutions)} combination(s) found.\n")
        for idx, solution in enumerate(all_solutions, 1):
            print(f"  [{idx}] {solution}")

    # process_tar_benchmarks("uf20-91.tar.gz")
    