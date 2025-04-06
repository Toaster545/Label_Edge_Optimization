# solve_worker.py
import traceback
from PyQt5 import QtCore
from simulated_annealing import (
    process_selected_pos,
    filter_inventory,
    compute_initial_solution,
    local_search_solution,
    is_valid_solution,
    createMasterDict,
)
from milp import optimize_assignment  # Import the MILP optimization function
from column_gen import optimize_assignment_column_generation  # Import the Column Generation optimization function

class SolveWorker(QtCore.QObject):
    progressChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(object)
    errorOccurred = QtCore.pyqtSignal(str)
    
    def __init__(self, inv_df, po_df, selected_pos, label_code, util_tol, rem_tol, len_tol, num_restarts, iterations, algorithm="SA"):
        """
        Parameters:
          - algorithm: A string flag to choose the optimization method.
                       "SA" for Simulated Annealing (default), "MILP" for MILP optimization,
                       or "COLGEN" for a column generation based approach.
        """
        super().__init__()
        self.inv_df = inv_df
        self.po_df = po_df
        self.selected_pos = selected_pos
        self.label_code = label_code
        self.util_tol = util_tol
        self.rem_tol = rem_tol
        self.len_tol = len_tol
        self.num_restarts = num_restarts
        self.iterations = iterations
        self.algorithm = algorithm  # "SA", "MILP", or "COLGEN"
        self._isCanceled = False
        
    def cancel(self):
        self._isCanceled = True
        
    def run(self):
        try:
            best_overall_waste = float('inf')
            best_overall_masters = None
            products, total_msi = process_selected_pos(self.selected_pos)
            
            keys = ['Paper', 'Width', 'Length', 'Nb', 'msi']
            products_dict = [dict(zip(keys, item.split('/'))) for item in self.selected_pos]
            
            original_product_count = len(products)
            filtered_inv = filter_inventory(self.inv_df, self.label_code)
            
            initial_masters = createMasterDict(inv_df= filtered_inv, prod_list_length=products[0][1])
            
            print("Algorithm:", self.algorithm)
            # Switch between optimization methods based on the algorithm flag.
            if self.algorithm.upper() == "MILP":
                
                masters = optimize_assignment(initial_masters, products_dict)
                self.progressChanged.emit(100)
                best_overall_masters = masters
            elif self.algorithm.upper() == "COLGEN":
                # Column Generation branch: use the column generation routine.
                masters = compute_initial_solution(filtered_inv, products, self.len_tol)
                masters = optimize_assignment_column_generation(initial_masters, products_dict)
                self.progressChanged.emit(100)
                best_overall_masters = masters
            else:
                # Simulated Annealing branch
                for restart in range(self.num_restarts):
                    if self._isCanceled:
                        self.finished.emit(None)
                        return
                    products_copy = products[:]  # make a copy of the products list
                    masters = compute_initial_solution(filtered_inv, products_copy, self.len_tol)
                    candidate_masters, candidate_waste = local_search_solution(
                        masters,
                        total_msi,
                        iterations=self.iterations,
                        lengthTol=self.len_tol,
                        initial_temp=1.0,
                        cooling_rate=0.99,
                    )
                    if candidate_waste < best_overall_waste:
                        best_overall_waste = candidate_waste
                        best_overall_masters = candidate_masters
                    progress_percent = int(100 * (restart + 1) / self.num_restarts)
                    self.progressChanged.emit(progress_percent)
            
            if best_overall_masters is None or not is_valid_solution(best_overall_masters, original_product_count):
                self.errorOccurred.emit("No solution found using current number of Products")
                self.finished.emit(None)
            else:
                self.finished.emit(best_overall_masters)
        except Exception:
            self.errorOccurred.emit(traceback.format_exc())
            self.finished.emit(None)
