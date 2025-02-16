# gui.py
from PyQt5 import QtWidgets, QtCore, QtGui
from labeledgeoptimiser.solution_dialog import SolutionDialog
from labeledgeoptimiser.solve_worker import SolveWorker
from labeledgeoptimiser.utils import createProductBlocks

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
        # Base page with products, papers, tolerances etc.
        self.init_base_page()
        # Start with the file settings page (index 0)
        self.stacked_widget.setCurrentIndex(0)
        
        self.solve_worker = None
        self.solve_thread = None

    def init_file_settings_page(self):
        """Page for setting file paths, PO filter threshold, and data filter variables."""
        self.settings_page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(self.settings_page)
        
        # --- Inventory Section ---
        # Inventory File Path
        self.inv_path_edit = QtWidgets.QLineEdit()
        browse_inv = QtWidgets.QPushButton("Browse")
        browse_inv.clicked.connect(self.browse_inv)
        inv_path_layout = QtWidgets.QHBoxLayout()
        inv_path_layout.addWidget(self.inv_path_edit)
        inv_path_layout.addWidget(browse_inv)
        layout.addRow("Inventory File:", inv_path_layout)
        
        # Inventory Data Filters (all on one row)
        inv_data_layout = QtWidgets.QHBoxLayout()
        
        # Inv Active Label
        inv_active_layout = QtWidgets.QVBoxLayout()
        inv_active_layout.addWidget(QtWidgets.QLabel("Inv Active Label:"))
        self.inv_active_label_edit = QtWidgets.QLineEdit()
        inv_active_layout.addWidget(self.inv_active_label_edit)
        inv_data_layout.addLayout(inv_active_layout)
        
        # Inv ID Label
        inv_id_layout = QtWidgets.QVBoxLayout()
        inv_id_layout.addWidget(QtWidgets.QLabel("Inv ID Label:"))
        self.inv_id_label_edit = QtWidgets.QLineEdit()
        inv_id_layout.addWidget(self.inv_id_label_edit)
        inv_data_layout.addLayout(inv_id_layout)
        
        # Inv Paper Label
        inv_paper_layout = QtWidgets.QVBoxLayout()
        inv_paper_layout.addWidget(QtWidgets.QLabel("Inv Paper Label:"))
        self.inv_paper_label_edit = QtWidgets.QLineEdit()
        inv_paper_layout.addWidget(self.inv_paper_label_edit)
        inv_data_layout.addLayout(inv_paper_layout)
        
        # Inv Width Label
        inv_width_layout = QtWidgets.QVBoxLayout()
        inv_width_layout.addWidget(QtWidgets.QLabel("Inv Width Label:"))
        self.inv_width_label_edit = QtWidgets.QLineEdit()
        inv_width_layout.addWidget(self.inv_width_label_edit)
        inv_data_layout.addLayout(inv_width_layout)
        
        # Inv Length Label
        inv_length_layout = QtWidgets.QVBoxLayout()
        inv_length_layout.addWidget(QtWidgets.QLabel("Inv Length Label:"))
        self.inv_length_label_edit = QtWidgets.QLineEdit()
        inv_length_layout.addWidget(self.inv_length_label_edit)
        inv_data_layout.addLayout(inv_length_layout)
        
        layout.addRow(inv_data_layout)
        
        # --- PO Section ---
        # PO File Path
        self.po_path_edit = QtWidgets.QLineEdit()
        browse_po = QtWidgets.QPushButton("Browse")
        browse_po.clicked.connect(self.browse_po)
        po_path_layout = QtWidgets.QHBoxLayout()
        po_path_layout.addWidget(self.po_path_edit)
        po_path_layout.addWidget(browse_po)
        layout.addRow("PO File:", po_path_layout)
        
        # PO Data Filters (all on one row)
        po_data_layout = QtWidgets.QHBoxLayout()
        
        # PO Active Label
        po_active_layout = QtWidgets.QVBoxLayout()
        po_active_layout.addWidget(QtWidgets.QLabel("PO Active Label:"))
        self.po_active_label_edit = QtWidgets.QLineEdit()
        po_active_layout.addWidget(self.po_active_label_edit)
        po_data_layout.addLayout(po_active_layout)
        
        # PO Number Label
        po_number_layout = QtWidgets.QVBoxLayout()
        po_number_layout.addWidget(QtWidgets.QLabel("PO Number Label:"))
        self.po_number_label_edit = QtWidgets.QLineEdit()
        po_number_layout.addWidget(self.po_number_label_edit)
        po_data_layout.addLayout(po_number_layout)
        
        # PO Start Column Label
        po_start_col_layout = QtWidgets.QVBoxLayout()
        po_start_col_layout.addWidget(QtWidgets.QLabel("PO Start Column Label:"))
        self.po_start_col_label_edit = QtWidgets.QLineEdit()
        po_start_col_layout.addWidget(self.po_start_col_label_edit)
        po_data_layout.addLayout(po_start_col_layout)
        
        # PO Company Label
        po_company_layout = QtWidgets.QVBoxLayout()
        po_company_layout.addWidget(QtWidgets.QLabel("PO Company Label:"))
        self.po_company_label_edit = QtWidgets.QLineEdit()
        po_company_layout.addWidget(self.po_company_label_edit)
        po_data_layout.addLayout(po_company_layout)
        
        # PO Order Label
        po_order_layout = QtWidgets.QVBoxLayout()
        po_order_layout.addWidget(QtWidgets.QLabel("PO Order Label:"))
        self.po_order_label_edit = QtWidgets.QLineEdit()
        po_order_layout.addWidget(self.po_order_label_edit)
        po_data_layout.addLayout(po_order_layout)
        
        layout.addRow(po_data_layout)
        
        # --- Bottom Section ---
        # PO Filter Threshold
        self.po_filter_edit = QtWidgets.QLineEdit("305")
        layout.addRow("PO Filter Threshold:", self.po_filter_edit)
        
        # Load Files Button
        load_btn = QtWidgets.QPushButton("Load Files")
        load_btn.clicked.connect(self.load_files)
        layout.addRow(load_btn)
        
        self.load_config()
        
        self.stacked_widget.addWidget(self.settings_page)



    def browse_inv(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Inventory File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)"
        )
        if filename:
            self.inv_path_edit.setText(filename)
    
    def browse_po(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select PO File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)"
        )
        if filename:
            self.po_path_edit.setText(filename)
    
    def load_config(self):
        import configparser, os
        from labeledgeoptimiser.config_utils import get_config_path
        self.config = configparser.ConfigParser()
        config_file = get_config_path()
        print("Loading config from:", config_file)
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            # Create default config if it doesn't exist
            self.config["Paths"] = {"inventory": "", "po": ""}
            self.config["Filters"] = {"po_threshold": "305"}
            self.config["Inv_data"] = {
                "active_label": "Actif / Inactif",
                "id_label": "Roll ID",
                "paper_label": "Code LabelEdge",
                "width_label": "Larg.",
                "length_label": "Longueur"
            }
            self.config["Po_data"] = {
                "active_label": "Actif / Inactif",
                "number_label": "No",
                "start_col_label": "Code Prix 1",
                "company_label": "Vendu à",
                "order_label": "No Commande"
            }
        print("Loaded sections in load_config:", self.config.sections())
        
        self.inv_path_edit.setText(self.config.get("Paths", "inventory", fallback=""))
        self.po_path_edit.setText(self.config.get("Paths", "po", fallback=""))
        self.po_filter_edit.setText(self.config.get("Filters", "po_threshold", fallback="305"))
        
        self.inv_active_label_edit.setText(self.config.get("Inv_data", "active_label", fallback="Actif / Inactif"))
        self.inv_id_label_edit.setText(self.config.get("Inv_data", "id_label", fallback="Roll ID"))
        self.inv_paper_label_edit.setText(self.config.get("Inv_data", "paper_label", fallback="Code LabelEdge"))
        self.inv_width_label_edit.setText(self.config.get("Inv_data", "width_label", fallback="Larg."))
        self.inv_length_label_edit.setText(self.config.get("Inv_data", "length_label", fallback="Longueur"))
        
        self.po_active_label_edit.setText(self.config.get("Po_data", "active_label", fallback="Actif / Inactif"))
        self.po_number_label_edit.setText(self.config.get("Po_data", "number_label", fallback="No"))
        self.po_start_col_label_edit.setText(self.config.get("Po_data", "start_col_label", fallback="Code Prix 1"))
        self.po_company_label_edit.setText(self.config.get("Po_data", "company_label", fallback="Vendu à"))
        self.po_order_label_edit.setText(self.config.get("Po_data", "order_label", fallback="No Commande"))
    
    def save_config(self):
        self.config["Paths"] = {"inventory": self.inv_path_edit.text(), "po": self.po_path_edit.text()}
        self.config["Filters"] = {"po_threshold": self.po_filter_edit.text()}
        self.config["Inv_data"] = {
            "active_label": self.inv_active_label_edit.text(),
            "id_label": self.inv_id_label_edit.text(),
            "paper_label": self.inv_paper_label_edit.text(),
            "width_label": self.inv_width_label_edit.text(),
            "length_label": self.inv_length_label_edit.text()
        }
        self.config["Po_data"] = {
            "active_label": self.po_active_label_edit.text(),
            "number_label": self.po_number_label_edit.text(),
            "start_col_label": self.po_start_col_label_edit.text(),
            "company_label": self.po_company_label_edit.text(),
            "order_label": self.po_order_label_edit.text()
        }
        with open("config.ini", "w") as f:
            self.config.write(f)
    
    def load_files(self):
        self.save_config()
        try:
            from labeledgeoptimiser.fileInput import xlsm_to_dataframe, filter_inv_df, filter_po_df
            self.inv_df = xlsm_to_dataframe(
                xlsm_file=self.inv_path_edit.text(), sheet_name="Papier", start_row=3
            )
            self.inv_df = filter_inv_df(
                self.inv_df,
                activeLabel=self.inv_active_label_edit.text(),
                idLabel=self.inv_id_label_edit.text(),
                paperLabel=self.inv_paper_label_edit.text(),
                widthLabel=self.inv_width_label_edit.text(),
                lengthLabel=self.inv_length_label_edit.text()
            )
            self.po_df = xlsm_to_dataframe(
                xlsm_file=self.po_path_edit.text(), sheet_name="PO Client", start_row=1
            )
            po_threshold = int(self.po_filter_edit.text())
            self.po_df = filter_po_df(
                self.po_df,
                po_threshold,
                activeLabel=self.po_active_label_edit.text(),
                numberLabel=self.po_number_label_edit.text(),
                startColLabel=self.po_start_col_label_edit.text(),
                companyLabel=self.po_company_label_edit.text(),
                orderLabel=self.po_order_label_edit.text()
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return
        # Proceed to order selection
        self.choose_orders()
    
    def init_base_page(self):
        """Base page that displays products, papers, and controls."""
        self.base_page = QtWidgets.QWidget()
        self.base_layout = QtWidgets.QVBoxLayout(self.base_page)
        self.stacked_widget.addWidget(self.base_page)
    
    def choose_orders(self):
        po_list = (
            self.po_df['No'].astype(str) + " " +
            self.po_df['Vendu à'].astype(str) + " " +
            self.po_df['No Commande'].astype(str)
        ).tolist()
        dlg = OrderSelectionDialog(po_list, self.po_df, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.products = dlg.get_products()
            self.update_base_layout()
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
    
        # Input fields for percentages and tolerances
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
