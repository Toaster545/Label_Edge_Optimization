from fileInput import xlsm_to_dataframe, filter_inv_df, process_groups, filter_po_df
from gui import createGui
import warnings
import tkinter as tk

def main():
    

    # Loading files
    xlsm_file = "data/Inventaire_2025.xlsx"
    sheet_name = "Papier"
    #use_columns = ['Code LabelEdge', 'Actif / Inactif','Larg.', 'Unit', 'Longueur', 'Unit2']
    inv_df = xlsm_to_dataframe(xlsm_file=xlsm_file, sheet_name=sheet_name, start_row=3)
    
    label_code = "S21-1"
    inv_df = filter_inv_df(inv_df, label_code)
    #print(inv_df)
    
    xlsm_file = "data/Commande_Client.xlsm"
    sheet_name = "PO Client"
    po_df = xlsm_to_dataframe(xlsm_file=xlsm_file, sheet_name=sheet_name, start_row=1)
    po_df = filter_po_df(po_df, 305)
    
    print(po_df)
    
    createGui(po_df)
    
    
    #code_values = inv_df["Code LabelEdge"].unique()
    # Print the unique values
    #print("Unique code values in 'Code LabelEdge':")
    #print(code_values)
    

if __name__ == "__main__":
    main()