import PySimpleGUI as sg
import sys
from algos import solve

def createGui(po_df, inv_df):
# create the gui for the application start

    selected_items = []
    po_list = (po_df['No'].astype(str) + " " + po_df['Vendu à'].astype(str) + " " +  po_df['No Commande'].astype(str)).tolist()
    
    layout = [
    [sg.Text("Select an option from the dropdown:")],
    [sg.Combo(po_list, key='-DROPDOWN-',default_value=po_list[0], enable_events=True)],
    [sg.Button("Add")], 
    [sg.Listbox(values=selected_items, size=(30, 6), key='-LISTBOX-')],
    [sg.Button("Submit"), sg.Button("Exit")]
]
    window = sg.Window("LabelEdge Optimiser", layout, size=(800, 600))

    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break
        
        if event == 'Add':
            selected_option = values['-DROPDOWN-']  # Get selected dropdown value
            if selected_option not in selected_items:
                selected_items.append(selected_option)  # Add to the list
                window['-LISTBOX-'].update(selected_items)  # Update the Listbox
        
        if event == "Submit":
            value = solve(inv_df=inv_df, po_df=po_df ,selected_pos=selected_items)
    window.close()