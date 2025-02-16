# solve_worker.py
import traceback
from PyQt5 import QtCore
from labeledgeoptimiser.simulated_annealing import process_selected_pos, filter_inventory, compute_initial_solution, local_search_solution, is_valid_solution

class SolveWorker(QtCore.QObject):
    progressChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(object)
    errorOccurred = QtCore.pyqtSignal(str)
    
    def __init__(self, inv_df, po_df, selected_pos, label_code, util_tol, rem_tol, len_tol, num_restarts, iterations):
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
        self._isCanceled = False
        
    def cancel(self):
        self._isCanceled = True
        
    def run(self):
        try:
            best_overall_waste = float('inf')
            best_overall_masters = None
            products, total_msi = process_selected_pos(self.selected_pos)
            original_product_count = len(products)
            filtered_inv = filter_inventory(self.inv_df, self.label_code)
            
            for restart in range(self.num_restarts):
                if self._isCanceled:
                    self.finished.emit(None)
                    return
                products_copy = products[:]
                masters = compute_initial_solution(filtered_inv, products_copy, self.len_tol)
                candidate_masters, candidate_waste = local_search_solution(
                    masters, total_msi, iterations=self.iterations, lengthTol=self.len_tol,
                    initial_temp=1.0, cooling_rate=0.99
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
        except Exception as e:
            self.errorOccurred.emit(traceback.format_exc())
            self.finished.emit(None)
