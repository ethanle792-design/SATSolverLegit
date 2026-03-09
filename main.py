import tarfile
import time
from engine import SATSolver

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
    process_tar_benchmarks("uf20-91.tar.gz")