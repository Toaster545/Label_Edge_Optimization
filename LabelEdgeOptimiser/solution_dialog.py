# solution_dialog.py
from PyQt5 import QtWidgets, QtGui
import pandas as pd
import simulated_annealing as sa

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
                table_data.append(
                    [master['Code'], master['Width'], master['Length'], f"{waste:.2f}%", master_msi, block_msi] 
                    + product_widths
                )
        column_headers = (
            ["Master ID", "Width", "Length", "Waste", "Master MSI", "Block MSI"] + 
            [f"Product {i+1}" for i in range(max_products)]
        )
        df = pd.DataFrame(table_data, columns=column_headers).fillna("-")
        df = df.sort_values(by="Master ID", ascending=False)
        return df
    
    def download_dataframe(self, df):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Solution", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if filename:
            try:
                df.to_csv(filename, index=False)
                QtWidgets.QMessageBox.information(self, "Success", f"Solution saved to {filename}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
