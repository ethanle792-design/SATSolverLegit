from engine import SATSolver
from convert_to_POS import BooleanLogicParser
from LogicSolver import LogicSolver
from utils import SATSolverUtils


if __name__ == "__main__":

    # # Initialize components
    parser = BooleanLogicParser()
    logic_wrapper = LogicSolver(parser, SATSolver)

    # Define your problem
    my_string = "(x1 AND x2) OR (x3 and x1) OR (x2 XOR ~x4)"
    my_assumptions = {} # e.g., {"x2": -1} to force x2 False

    # Solve
    all_solutions = logic_wrapper.solve_all(my_string, my_assumptions)

    # Output
    print(f"Expression:  {my_string}")
    print(f"Assumptions: {my_assumptions}")

    if not all_solutions:
        print("Status:      UNSAT — no satisfying assignment exists.")
    else:
        print(f"Status:      SATISFIABLE — {len(all_solutions)} combination(s) found.\n")
        for idx, solution in enumerate(all_solutions, 1):
            print(f"  [{idx}] {solution}")
    # --- Working with Solutions ---
    essential, _ = SATSolverUtils.get_minimal_assignments(solution)
    print(f"\nMinimal Set: {essential}")
    
    #SATSolverUtils.process_tar_benchmarks("uuf100-430.tar.gz", SATSolver)
    