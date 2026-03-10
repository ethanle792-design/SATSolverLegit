from engine import SATSolver
from convert_to_POS import BooleanLogicParser
from LogicSolver import LogicSolver
from utils import SATSolverUtils


if __name__ == "__main__":

    # Initialize 
    parser = BooleanLogicParser()
    logic_wrapper = LogicSolver(parser, SATSolver)

    # input/define the problem expression
    my_string = input("Enter the Boolean expression: ")
    my_assumptions = {} # e.g., {"x2": -1} to force x2 False

    # Solve given expression
    all_solutions = logic_wrapper.solve_all(my_string, my_assumptions)
    minimal = logic_wrapper.get_minimal(all_solutions)

    # Print initial data 
    print(f"Expression:  {my_string}")
    print(f"Assumptions: {my_assumptions}")

    # Print SAT results
    if not all_solutions:
        print("Status:      UNSAT — no satisfying assignment exists.")
    else:
        print(f"Status:      SATISFIABLE — {len(all_solutions)} combination(s) found.\n")
        for index1, solution in enumerate(all_solutions, 1):
            print(f"  [{index1}] {solution}")
            
        print(f"\nMinimal Set of Variables:")
        for index2, reduced in enumerate(minimal, 1):
            print(f"  [{index2}] {reduced}")
    
    
    #SATSolverUtils.process_tar_benchmarks("uuf100-430.tar.gz", SATSolver)
    