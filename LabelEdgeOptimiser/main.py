import sys
import os
import configparser
from PyQt5 import QtWidgets
from labeledgeoptimiser.gui import MainWindow
from labeledgeoptimiser.fileInput import xlsm_to_dataframe, filter_inv_df, filter_po_df
from labeledgeoptimiser.config_utils import get_config_path

CONFIG_FILE = "config.ini"

def main():
    """ Main entry point for the application """

    app = QtWidgets.QApplication(sys.argv)  # This must be initialized before creating any QWidget

    config = configparser.ConfigParser()
    config_path = get_config_path()
    print("DEBUG: Looking for config file at:", config_path)
    if os.path.exists(config_path):
        files_read = config.read(config_path)
        print("Config files read:", files_read)
    else:
        print("Config file not found. Creating default config.")

    if not config.has_section("Paths"):
        config["Paths"] = {"inventory": "", "po": ""}
    if not config.has_section("Filters"):
        config["Filters"] = {"po_threshold": "305"}
    if not config.has_section("Inv_data"):
        config["Inv_data"] = {
            "active_label": "Actif / Inactif",
            "id_label": "Roll ID",
            "paper_label": "Code LabelEdge",
            "width_label": "Larg.",
            "length_label": "Longueur"
        }
    if not config.has_section("Po_data"):
        config["Po_data"] = {
            "active_label": "Actif / Inactif",
            "number_label": "No",
            "start_col_label": "Code Prix 1",
            "company_label": "Vendu à",
            "order_label": "No Commande"
        }

    inv_path = config["Paths"].get("inventory", "")
    po_path = config["Paths"].get("po", "")
    po_threshold = int(config["Filters"].get("po_threshold", "305"))
    print("Loaded sections:", config.sections())

    if not inv_path or not po_path:
        dlg = QtWidgets.QDialog()
        dlg.setWindowTitle("Select File Paths")
        dlg_layout = QtWidgets.QFormLayout(dlg)
        inv_edit = QtWidgets.QLineEdit()
        po_edit = QtWidgets.QLineEdit()
        po_threshold_edit = QtWidgets.QLineEdit(str(po_threshold))
        browse_inv = QtWidgets.QPushButton("Browse")
        browse_po = QtWidgets.QPushButton("Browse")

        def browse_inv_func():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                dlg, "Select Inventory File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)"
            )
            if filename:
                inv_edit.setText(filename)

        def browse_po_func():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(
                dlg, "Select PO File", "", "Excel Files (*.xlsx *.xlsm);;All Files (*)"
            )
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
            config["Filters"]["po_threshold"] = str(po_threshold)
            with open(CONFIG_FILE, "w") as f:
                config.write(f)
        else:
            sys.exit(0)

    try:
        sheet_inv = "Papier"
        sheet_po = "PO Client"
        print(f"Reading File: {inv_path}")
        inv_df = xlsm_to_dataframe(xlsm_file=inv_path, sheet_name=sheet_inv, start_row=3)

        # Inventory filters from config
        inv_active_label = config["Inv_data"].get("active_label", "Actif / Inactif")
        inv_id_label = config["Inv_data"].get("id_label", "Roll ID")
        inv_paper_label = config["Inv_data"].get("paper_label", "Code LabelEdge")
        inv_width_label = config["Inv_data"].get("width_label", "Larg.")
        inv_length_label = config["Inv_data"].get("length_label", "Longueur")
        inv_df = filter_inv_df(
            inv_df,
            activeLabel=inv_active_label,
            idLabel=inv_id_label,
            paperLabel=inv_paper_label,
            widthLabel=inv_width_label,
            lengthLabel=inv_length_label
        )

        print(f"Reading File: {po_path}")
        po_df = xlsm_to_dataframe(xlsm_file=po_path, sheet_name=sheet_po, start_row=1)

        # PO filters from config
        po_active_label = config["Po_data"].get("active_label", "Actif / Inactif")
        number_label = config["Po_data"].get("number_label", "No")
        start_col_label = config["Po_data"].get("start_col_label", "Code Prix 1")
        company_label = config["Po_data"].get("company_label", "Vendu à")
        order_label = config["Po_data"].get("order_label", "No Commande")
        po_df = filter_po_df(
            po_df,
            po_threshold,
            activeLabel=po_active_label,
            numberLabel=number_label,
            startColLabel=start_col_label,
            companyLabel=company_label,
            orderLabel=order_label
        )

    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error", f"Failed to load data: {e}")
        sys.exit(1)

    main_window = MainWindow(po_df, inv_df)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
