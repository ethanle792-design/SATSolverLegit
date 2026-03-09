from engine import SATSolver
from convert_to_POS import BooleanLogicParser
from LogicSolver import LogicSolver
from utils import SATSolverUtils

if __name__ == "__main__":

    # # Initialize components
    # parser = BooleanLogicParser()
    # logic_wrapper = LogicSolver(parser, SATSolver)

    # # Define your problem
    # my_string = "(~x1 OR x2) AND (x3 or ~x4) AND x1"
    # my_assumptions = {} # e.g., {"x2": -1} to force x2 False

    # # Solve
    # result, solution = logic_wrapper.solve_expression(my_string, my_assumptions)

    # # Output
    # print(f"Expression: {my_string}")
    # print(f"Assumptions: {my_assumptions}")
    # print(f"Status:      {result}")
    
    # if result == "SATISFIABLE":
    #     print(f"Solution:    {solution}")
        
    # # --- Working with Solutions ---
    # essential, _ = SATSolverUtils.get_minimal_assignments(solution)
    # print(f"\nMinimal Set: {essential}")
    
    SATSolverUtils.process_tar_benchmarks("uuf100-430.tar.gz", SATSolver)
    
