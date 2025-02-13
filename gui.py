import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from algos import solve, createProductBlocks

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

        # Header
        header = QtWidgets.QLabel("Check all wanted orders")
        header.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Bold))
        main_layout.addWidget(header)

        # Scrollable area for order checkboxes
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QtWidgets.QWidget()
        self.orders_layout = QtWidgets.QVBoxLayout(scroll_content)
        self.checkboxes = []

        for i, order in enumerate(po_list):
            cb = QtWidgets.QCheckBox(order)
            self.checkboxes.append(cb)
            self.orders_layout.addWidget(cb)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Buttons: Back and Submit
        btn_layout = QtWidgets.QHBoxLayout()
        back_btn = QtWidgets.QPushButton("Back")
        back_btn.clicked.connect(self.reject)  # Cancel the dialog
        submit_btn = QtWidgets.QPushButton("Submit")
        submit_btn.clicked.connect(self.submit)
        btn_layout.addWidget(back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(submit_btn)
        main_layout.addLayout(btn_layout)

    def submit(self):
        # Gather checked orders
        self.selected_orders = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        # Create product blocks based on the selected orders
        self.products = createProductBlocks(self.po_df, self.selected_orders)
        self.accept()

    def get_products(self):
        return self.products


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

        # Use a QStackedWidget to hold different "pages" of the UI.
        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        main_layout.addWidget(self.stacked_widget)

        self.init_initial_page()
        self.init_base_page()  # Create the base page (it will be updated later)
        self.stacked_widget.setCurrentIndex(0)

    def init_initial_page(self):
        """Initial page with the 'Choose Orders' button."""
        self.initial_page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.initial_page)
        layout.addStretch()
        self.choose_orders_button = QtWidgets.QPushButton("Choose Orders")
        self.choose_orders_button.setFixedSize(150, 50)
        self.choose_orders_button.clicked.connect(self.choose_orders)
        layout.addWidget(self.choose_orders_button, alignment=QtCore.Qt.AlignCenter)
        layout.addStretch()
        self.stacked_widget.addWidget(self.initial_page)

    def init_base_page(self):
        """Base page that will display products, papers, and input fields."""
        self.base_page = QtWidgets.QWidget()
        self.base_layout = QtWidgets.QVBoxLayout(self.base_page)
        # Initially empty; will be populated after orders are chosen.
        self.stacked_widget.addWidget(self.base_page)

    def choose_orders(self):
        """Open the order selection dialog."""
        po_list = (self.po_df['No'].astype(str) + " " +
                   self.po_df['Vendu à'].astype(str) + " " +
                   self.po_df['No Commande'].astype(str)).tolist()

        dlg = OrderSelectionDialog(po_list, self.po_df, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.products = dlg.get_products()
            self.update_base_layout()
            self.stacked_widget.setCurrentIndex(1)
        # If the dialog is rejected (via its Back button), do nothing;
        # the user remains on the initial page.

    def update_base_layout(self):
        """Build the main (base) UI with products, papers, inputs, and buttons."""
        # Clear any existing content in the base layout
        for i in reversed(range(self.base_layout.count())):
            item = self.base_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            else:
                self.clear_layout(item.layout())

        # Create the products/papers view
        content_layout = QtWidgets.QHBoxLayout()

        # Left: Products (as checkboxes inside a scroll area)
        product_group = QtWidgets.QGroupBox("Products")
        self.product_layout = QtWidgets.QVBoxLayout()
        self.product_checkboxes = []
        for prod in self.products:
            cb = QtWidgets.QCheckBox(prod)
            self.product_checkboxes.append(cb)
            self.product_layout.addWidget(cb)
        product_group.setLayout(self.product_layout)
        product_scroll = QtWidgets.QScrollArea()
        product_scroll.setWidget(product_group)
        product_scroll.setWidgetResizable(True)
        product_scroll.setFixedSize(250, 300)
        content_layout.addWidget(product_scroll)

        # Right: Papers (as radio buttons inside a scroll area)
        paper_group = QtWidgets.QGroupBox("Papers")
        paper_layout = QtWidgets.QVBoxLayout()
        self.paper_button_group = QtWidgets.QButtonGroup(self)
        papers = sorted([p for p in self.inv_df['Code LabelEdge'].dropna().unique()])
        for i, paper in enumerate(papers):
            rb = QtWidgets.QRadioButton(paper)
            if i == 2:  # Pre-select the third paper, if available
                rb.setChecked(True)
            self.paper_button_group.addButton(rb, i)
            paper_layout.addWidget(rb)
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
        self.rem_input = QtWidgets.QLineEdit("0.1")
        input_layout.addWidget(full_label)
        input_layout.addWidget(self.full_input)
        input_layout.addSpacing(20)
        input_layout.addWidget(rem_label)
        input_layout.addWidget(self.rem_input)
        self.base_layout.addLayout(input_layout)

        # Input fields for restarts and iterations
        input_layout2 = QtWidgets.QHBoxLayout()
        restarts_label = QtWidgets.QLabel("Restarts:")
        self.restarts_input = QtWidgets.QLineEdit("300")
        iterations_label = QtWidgets.QLabel("Iterations:")
        self.iterations_input = QtWidgets.QLineEdit("10")
        input_layout2.addWidget(restarts_label)
        input_layout2.addWidget(self.restarts_input)
        input_layout2.addSpacing(20)
        input_layout2.addWidget(iterations_label)
        input_layout2.addWidget(self.iterations_input)
        self.base_layout.addLayout(input_layout2)

        # Buttons: Back, Remove, Submit, Exit
        btn_layout = QtWidgets.QHBoxLayout()
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.clicked.connect(self.back_to_initial)
        self.remove_button = QtWidgets.QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_selected_products)
        self.submit_button = QtWidgets.QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit)
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
        """Switch back to the initial page with the 'Choose Orders' button."""
        self.stacked_widget.setCurrentIndex(0)

    def remove_selected_products(self):
        """Remove any product checkboxes that are checked."""
        for cb in self.product_checkboxes[:]:
            if cb.isChecked():
                self.product_layout.removeWidget(cb)
                cb.deleteLater()
                self.product_checkboxes.remove(cb)

    def submit(self):
        # Gather selected products
        selected_products = [cb.text() for cb in self.product_checkboxes if cb.isChecked()]
        # Get the selected paper
        selected_button = self.paper_button_group.checkedButton()
        if selected_button is None:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a paper.")
            return
        selected_paper_value = selected_button.text()

        try:
            util_tol = float(self.full_input.text())
            rem_tol = float(self.rem_input.text())
            restarts = int(self.restarts_input.text())
            iterations = int(self.iterations_input.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid input for tolerances or iterations.")
            return

        # Call the solve function
        result = solve(
            inv_df=self.inv_df,
            po_df=self.po_df,
            selected_pos=selected_products,
            label_code=selected_paper_value,
            util_tol=util_tol,
            rem_tol=rem_tol,
            num_restarts=restarts,
            iterations=iterations,
        )
        QtWidgets.QMessageBox.information(self, "Result", "Solve function executed.")

def createGui(po_df, inv_df):
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(po_df, inv_df)
    window.show()
    sys.exit(app.exec_())

