import sys, os, copy, random, math, traceback, configparser
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from algos import createProductBlocks, process_selected_pos, filter_inventory, print_masters_table
import simulated_annealing as sa  # Assumes your SA-based solve() and related functions are here
from fileInput import xlsm_to_dataframe, filter_inv_df, filter_po_df

CONFIG_FILE = "config.ini"

########################################
# Worker for Asynchronous Solve
########################################
class SolveWorker(QtCore.QObject):
    progressChanged = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(object)
    errorOccurred = QtCore.pyqtSignal(str)
    
    def __init__(self, inv_df, po_df, selected_pos, label_code, 
                 util_tol, rem_tol, len_tol, num_restarts, iterations):
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
                masters = sa.compute_initial_solution(filtered_inv, products_copy, self.len_tol)
                candidate_masters, candidate_waste = sa.local_search_solution(
                    masters, total_msi, iterations=self.iterations, lengthTol=self.len_tol,
                    initial_temp=1.0, cooling_rate=0.99
                )
                if candidate_waste < best_overall_waste:
                    best_overall_waste = candidate_waste
                    best_overall_masters = candidate_masters
                progress_percent = int(100 * (restart + 1) / self.num_restarts)
                self.progressChanged.emit(progress_percent)
            
            if best_overall_masters is None or not sa.is_valid_solution(best_overall_masters, original_product_count):
                self.errorOccurred.emit("No solution found using current number of Products")
                self.finished.emit(None)
            else:
                self.finished.emit(best_overall_masters)
        except Exception as e:
            self.errorOccurred.emit(traceback.format_exc())
            self.finished.emit(None)

########################################
# Dialog to Display the Solution
########################################
class SolutionDialog(QtWidgets.QDialog):
    def __init__(self, masters, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Solution")
        self.resize(800, 600)
        layout = QtWidgets.QVBoxLayout(self)
        
        overall_waste = sa.calculateWaste(masters)
        waste_label = QtWidgets.QLabel(f"Overall Waste: {overall_waste:.2f}%")
        waste_label.setFont(QtGui.QFont("Arial", 12))
        layout.addWidget(waste_label)
        
        df = self.build_dataframe(masters)
        table = QtWidgets.QTableWidget()
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())
        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QtWidgets.QTableWidgetItem(str(df.iloc[i, j]))
                table.setItem(i, j, item)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        btn_layout = QtWidgets.QHBoxLayout()
        download_btn = QtWidgets.QPushButton("Download")
        download_btn.clicked.connect(lambda: self.download_dataframe(df))
        back_btn = QtWidgets.QPushButton("Back")
        back_btn.clicked.connect(self.close)
        exit_btn = QtWidgets.QPushButton("Exit")
        exit_btn.clicked.connect(QtWidgets.QApplication.instance().quit)
        btn_layout.addWidget(download_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)
    
    def build_dataframe(self, masters):
        table_data = []
        max_products = 0
        for master in masters:
            master_msi = (master['Width'] * master['Length'] * 12) / 1000
            for block, waste in zip(master['Products'], master['Waste']):
                if not block:
                    continue
                product_widths = sorted([p[0] for p in block], reverse=True)
                max_products = max(max_products, len(product_widths))
                block_msi = (sum(p[0] for p in block) * master['Length'] * 12) / 1000
                table_data.append([master['Code'], master['Width'], master['Length'], f"{waste:.2f}%", master_msi, block_msi] + product_widths)
        column_headers = ["Master ID", "Width", "Length", "Waste", "Master MSI", "Block MSI"] + [f"Product {i+1}" for i in range(max_products)]
        df = pd.DataFrame(table_data, columns=column_headers).fillna("-")
        df = df.sort_values(by="Master ID", ascending=False)
        return df
    
    def download_dataframe(self, df):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Solution", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filename:
            try:
                df.to_csv(filename, index=False)
                QtWidgets.QMessageBox.information(self, "Success", f"Solution saved to {filename}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

########################################
# Main Window with File Settings
########################################
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, po_df, inv_df):
        super().__init__()
        self.po_df = po_df
        self.inv_df = inv_df
        self.products = []  
        self.product_checkboxes = []
        self.setWindowTitle("LabelEdge Optimiser")
        self.resize(800, 600)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.stacked_widget)

        # File Settings Page
        self.init_file_settings_page()
        # Base page with products/papers/tolerances etc.
        self.init_base_page()
        # Start with the file settings page (index 0)
        self.stacked_widget.setCurrentIndex(0)
        
        self.solve_worker = None
        self.solve_thread = None

    def init_file_settings_page(self):
        """Page for setting file paths and the PO filter threshold."""
        self.settings_page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(self.settings_page)
        
        self.inv_path_edit = QtWidgets.QLineEdit()
        self.po_path_edit = QtWidgets.QLineEdit()
        
        browse_inv = QtWidgets.QPushButton("Browse")
        browse_inv.clicked.connect(self.browse_inv)
        browse_po = QtWidgets.QPushButton("Browse")
        browse_po.clicked.connect(self.browse_po)
        
        inv_layout = QtWidgets.QHBoxLayout()
        inv_layout.addWidget(self.inv_path_edit)
        inv_layout.addWidget(browse_inv)
        
        po_layout = QtWidgets.QHBoxLayout()
        po_layout.addWidget(self.po_path_edit)
        po_layout.addWidget(browse_po)
        
        layout.addRow("Inventory File:", inv_layout)
        layout.addRow("PO File:", po_layout)
        
        # New: PO Filter Threshold input
        self.po_filter_edit = QtWidgets.QLineEdit("305")
        layout.addRow("PO Filter Threshold:", self.po_filter_edit)
        
        load_btn = QtWidgets.QPushButton("Load Files")
        load_btn.clicked.connect(self.load_files)
        layout.addRow(load_btn)
        
        self.load_config()
        
        self.stacked_widget.addWidget(self.settings_page)

    def browse_inv(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Inventory File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)")
        if filename:
            self.inv_path_edit.setText(filename)
    
    def browse_po(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select PO File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)")
        if filename:
            self.po_path_edit.setText(filename)
    
    def load_config(self):
        self.config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
        else:
            self.config["Paths"] = {"inventory": "", "po": ""}
            self.config["Filters"] = {"po_threshold": "305"}
        self.inv_path_edit.setText(self.config["Paths"].get("inventory", ""))
        self.po_path_edit.setText(self.config["Paths"].get("po", ""))
        if "Filters" not in self.config:
            self.config["Filters"] = {"po_threshold": "305"}
        self.po_filter_edit.setText(self.config["Filters"].get("po_threshold", "305"))
    
    def save_config(self):
        self.config["Paths"] = {"inventory": self.inv_path_edit.text(), "po": self.po_path_edit.text()}
        if "Filters" not in self.config:
            self.config["Filters"] = {}
        self.config["Filters"]["po_threshold"] = self.po_filter_edit.text()
        with open(CONFIG_FILE, "w") as f:
            self.config.write(f)
    
    def load_files(self):
        self.save_config()
        try:
            self.inv_df = xlsm_to_dataframe(xlsm_file=self.inv_path_edit.text(), sheet_name="Papier", start_row=3)
            self.inv_df = filter_inv_df(self.inv_df, "S21-1")
            self.po_df = xlsm_to_dataframe(xlsm_file=self.po_path_edit.text(), sheet_name="PO Client", start_row=1)
            po_threshold = int(self.po_filter_edit.text())
            self.po_df = filter_po_df(self.po_df, po_threshold)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return
        # Instead of going to an intermediate "choose orders" page,
        # immediately open the order selection dialog.
        self.choose_orders()
    
    def init_base_page(self):
        """Base page that will display products, papers, inputs, and buttons."""
        self.base_page = QtWidgets.QWidget()
        self.base_layout = QtWidgets.QVBoxLayout(self.base_page)
        self.stacked_widget.addWidget(self.base_page)

    def choose_orders(self):
        po_list = (self.po_df['No'].astype(str) + " " +
                   self.po_df['Vendu à'].astype(str) + " " +
                   self.po_df['No Commande'].astype(str)).tolist()
        dlg = OrderSelectionDialog(po_list, self.po_df, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.products = dlg.get_products()
            self.update_base_layout()
            # Now that the orders have been chosen, switch to the base page.
            # (Note: With the removal of the initial page, base page is now at index 1.)
            self.stacked_widget.setCurrentIndex(1)

    def update_base_layout(self):
        for i in reversed(range(self.base_layout.count())):
            item = self.base_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            else:
                self.clear_layout(item.layout())

        content_layout = QtWidgets.QHBoxLayout()

        # Left: Products (checkboxes)
        product_group = QtWidgets.QGroupBox("Products")
        self.product_layout = QtWidgets.QVBoxLayout()
        self.product_checkboxes = []
        for prod in self.products:
            cb = QtWidgets.QCheckBox(prod)
            cb.setChecked(True)
            self.product_checkboxes.append(cb)
            self.product_layout.addWidget(cb)
        product_group.setLayout(self.product_layout)
        product_scroll = QtWidgets.QScrollArea()
        product_scroll.setWidget(product_group)
        product_scroll.setWidgetResizable(True)
        product_scroll.setFixedSize(250, 300)
        content_layout.addWidget(product_scroll)

        # Right: Papers (checkboxes)
        paper_group = QtWidgets.QGroupBox("Papers")
        paper_layout = QtWidgets.QVBoxLayout()
        self.paper_button_group = []
        papers = sorted([p for p in self.inv_df['Code LabelEdge'].dropna().unique()])
        for paper in papers:
            cb = QtWidgets.QCheckBox(paper)
            cb.setChecked(False)
            self.paper_button_group.append(cb)
            paper_layout.addWidget(cb)
        paper_group.setLayout(paper_layout)
        paper_scroll = QtWidgets.QScrollArea()
        paper_scroll.setWidget(paper_group)
        paper_scroll.setWidgetResizable(True)
        paper_scroll.setFixedSize(250, 300)
        content_layout.addWidget(paper_scroll)

        self.base_layout.addLayout(content_layout)

        # Input fields for percentages
        input_layout = QtWidgets.QHBoxLayout()
        full_label = QtWidgets.QLabel('Percentage of "Full" master roll:')
        self.full_input = QtWidgets.QLineEdit("0.8")
        rem_label = QtWidgets.QLabel("Max Removal Percentage:")
        self.rem_input = QtWidgets.QLineEdit("0.15")
        len_label = QtWidgets.QLabel("Length Tolerance:")
        self.len_input = QtWidgets.QLineEdit("0.3")
        input_layout.addWidget(full_label)
        input_layout.addWidget(self.full_input)
        input_layout.addSpacing(20)
        input_layout.addWidget(rem_label)
        input_layout.addWidget(self.rem_input)
        input_layout.addSpacing(20)
        input_layout.addWidget(len_label)
        input_layout.addWidget(self.len_input)
        self.base_layout.addLayout(input_layout)

        # Input fields for restarts and iterations
        input_layout2 = QtWidgets.QHBoxLayout()
        restarts_label = QtWidgets.QLabel("Restarts:")
        self.restarts_input = QtWidgets.QLineEdit("20")
        iterations_label = QtWidgets.QLabel("Iterations:")
        self.iterations_input = QtWidgets.QLineEdit("5000")
        input_layout2.addWidget(restarts_label)
        input_layout2.addWidget(self.restarts_input)
        input_layout2.addSpacing(20)
        input_layout2.addWidget(iterations_label)
        input_layout2.addWidget(self.iterations_input)
        self.base_layout.addLayout(input_layout2)

        # Progress bar and Cancel button
        progress_layout = QtWidgets.QHBoxLayout()
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_solve)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.cancel_button)
        self.base_layout.addLayout(progress_layout)

        # Buttons: Back, Remove, Submit, Exit
        btn_layout = QtWidgets.QHBoxLayout()
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.clicked.connect(self.back_to_initial)
        self.remove_button = QtWidgets.QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_products)
        self.submit_button = QtWidgets.QPushButton("Submit")
        self.submit_button.clicked.connect(self.start_solve)
        self.exit_button = QtWidgets.QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        btn_layout.addWidget(self.back_button)
        btn_layout.addWidget(self.remove_button)
        btn_layout.addWidget(self.submit_button)
        btn_layout.addWidget(self.exit_button)
        self.base_layout.addLayout(btn_layout)
        

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self.clear_layout(child.layout())

    def back_to_initial(self):
        # With the removal of the initial page, going "back" now returns to the file settings page.
        self.stacked_widget.setCurrentIndex(0)

    def remove_selected_products(self):
        for cb in self.product_checkboxes[:]:
            if cb.isChecked():
                self.product_layout.removeWidget(cb)
                cb.deleteLater()
                self.product_checkboxes.remove(cb)

    def start_solve(self):
        try:
            util_tol = float(self.full_input.text())
            rem_tol = float(self.rem_input.text())
            len_tol = float(self.len_input.text())
            restarts = int(self.restarts_input.text())
            iterations = int(self.iterations_input.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid input for tolerances or iterations.")
            return
        
        selected_products = [cb.text() for cb in self.product_checkboxes if cb.isChecked()]
        selected_papers = [cb.text() for cb in self.paper_button_group if cb.isChecked()]
        if not selected_papers:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select at least one paper.")
            return
        
        self.submit_button.setEnabled(False)
        
        self.solve_worker = SolveWorker(
            inv_df=self.inv_df,
            po_df=self.po_df,
            selected_pos=selected_products,
            label_code=selected_papers,
            util_tol=util_tol,
            rem_tol=rem_tol,
            len_tol=len_tol,
            num_restarts=restarts,
            iterations=iterations,
        )
        self.solve_worker.progressChanged.connect(self.progress_bar.setValue)
        self.solve_worker.finished.connect(self.handle_solve_finished)
        self.solve_worker.errorOccurred.connect(self.handle_solve_error)
        
        self.solve_thread = QtCore.QThread()
        self.solve_worker.moveToThread(self.solve_thread)
        self.solve_thread.started.connect(self.solve_worker.run)
        self.solve_thread.start()
    
    def cancel_solve(self):
        if self.solve_worker:
            self.solve_worker.cancel()
            self.cancel_button.setEnabled(False)
    
    def handle_solve_finished(self, result):
        self.solve_thread.quit()
        self.solve_thread.wait()
        self.submit_button.setEnabled(True)
        if result is None:
            QtWidgets.QMessageBox.information(self, "Result", "Solve was cancelled or no valid solution found.")
        else:
            dlg = SolutionDialog(result, self)
            dlg.exec_()
    
    def handle_solve_error(self, error_msg):
        QtWidgets.QMessageBox.critical(self, "Error", error_msg)

########################################
# Order Selection Dialog
########################################
class OrderSelectionDialog(QtWidgets.QDialog):
    def __init__(self, po_list, po_df, parent=None):
        super().__init__(parent)
        self.po_list = po_list
        self.po_df = po_df
        self.products = []
        self.selected_orders = []
        self.setWindowTitle("Order Selector")
        self.resize(800, 600)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel("Check all wanted orders")
        header.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        main_layout.addWidget(header)
        
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        self.orders_layout = QtWidgets.QVBoxLayout(scroll_content)
        self.checkboxes = []
        for order in po_list:
            cb = QtWidgets.QCheckBox(order)
            self.checkboxes.append(cb)
            self.orders_layout.addWidget(cb)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        btn_layout = QtWidgets.QHBoxLayout()
        back_btn = QtWidgets.QPushButton("Back")
        back_btn.clicked.connect(self.reject)
        submit_btn = QtWidgets.QPushButton("Submit")
        submit_btn.clicked.connect(self.submit)
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        main_layout.addLayout(btn_layout)
    
    def submit(self):
        self.selected_orders = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        self.products = createProductBlocks(self.po_df, self.selected_orders)
        self.accept()
    
    def get_products(self):
        return self.products

########################################
# Main Application GUI and Main Function
########################################
def createGui(po_df, inv_df):
    app = QtWidgets.QApplication(sys.argv)
    
    # Load external stylesheet
    try:
        with open("styles.qss", "r") as style_file:
            app.setStyleSheet(style_file.read())
    except Exception as e:
        print("Could not load stylesheet:", e)
    
    window = MainWindow(po_df, inv_df)
    window.show()
    sys.exit(app.exec_())


def main():
    # Load file paths and PO filter threshold from config.ini
    import configparser
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config["Paths"] = {"inventory": "", "po": ""}
        config["Filters"] = {"po_threshold": "305"}
    inv_path = config["Paths"].get("inventory", "")
    po_path = config["Paths"].get("po", "")
    if "Filters" in config and "po_threshold" in config["Filters"]:
        po_threshold = int(config["Filters"]["po_threshold"])
    else:
        po_threshold = 305
    
    # If paths are not set, prompt the user to select files and PO threshold.
    if not inv_path or not po_path:
        app = QtWidgets.QApplication(sys.argv)
        dlg = QtWidgets.QDialog()
        dlg.setWindowTitle("Select File Paths")
        dlg_layout = QtWidgets.QFormLayout(dlg)
        inv_edit = QtWidgets.QLineEdit()
        po_edit = QtWidgets.QLineEdit()
        po_threshold_edit = QtWidgets.QLineEdit(str(po_threshold))
        browse_inv = QtWidgets.QPushButton("Browse")
        browse_po = QtWidgets.QPushButton("Browse")
        def browse_inv_func():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(dlg, "Select Inventory File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)")
            if filename:
                inv_edit.setText(filename)
        def browse_po_func():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(dlg, "Select PO File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)")
            if filename:
                po_edit.setText(filename)
        browse_inv.clicked.connect(browse_inv_func)
        browse_po.clicked.connect(browse_po_func)
        inv_layout = QtWidgets.QHBoxLayout()
        inv_layout.addWidget(inv_edit)
        inv_layout.addWidget(browse_inv)
        po_layout = QtWidgets.QHBoxLayout()
        po_layout.addWidget(po_edit)
        po_layout.addWidget(browse_po)
        dlg_layout.addRow("Inventory File:", inv_layout)
        dlg_layout.addRow("PO File:", po_layout)
        dlg_layout.addRow("PO Filter Threshold:", po_threshold_edit)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        dlg_layout.addRow(button_box)
        button_box.accepted.connect(dlg.accept)
        button_box.rejected.connect(dlg.reject)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            inv_path = inv_edit.text()
            po_path = po_edit.text()
            po_threshold = int(po_threshold_edit.text())
            config["Paths"]["inventory"] = inv_path
            config["Paths"]["po"] = po_path
            if "Filters" not in config:
                config["Filters"] = {}
            config["Filters"]["po_threshold"] = str(po_threshold)
            with open(CONFIG_FILE, "w") as f:
                config.write(f)
        else:
            sys.exit(0)
    
    # Load the data files using fileInput functions
    from fileInput import xlsm_to_dataframe  # Assuming these functions exist in fileInput
    sheet_inv = "Papier"
    sheet_po = "PO Client"
    inv_df = xlsm_to_dataframe(xlsm_file=inv_path, sheet_name=sheet_inv, start_row=3)
    inv_df = filter_inv_df(inv_df, "S21-1")
    po_df = xlsm_to_dataframe(xlsm_file=po_path, sheet_name=sheet_po, start_row=1)
    po_df = filter_po_df(po_df, po_threshold)
    
    createGui(po_df, inv_df)

if __name__ == "__main__":
    main()
