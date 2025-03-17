import sys
import os
import configparser
from PyQt5 import QtWidgets
from gui import MainWindow
from fileInput import xlsm_to_dataframe, filter_inv_df, filter_po_df
from config_utils import get_config_path

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

    # Set default configurations
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
    if not config.has_section("Optimization"):
        config["Optimization"] = {"algorithm": "MILP"}
        

    # Create empty DataFrames as placeholders
    import pandas as pd
    inv_df = pd.DataFrame()
    po_df = pd.DataFrame()
    # Create and show the main window
    main_window = MainWindow(po_df, inv_df)
    main_window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()