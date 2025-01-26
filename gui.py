import PySimpleGUI as sg
import sys

def createGui(po_df):
# create the gui for the application start

    sg.theme('DarkBlue3')
    
    selected_orders = []
    po_list = (po_df['No'].astype(str) + " " + po_df['Vendu à'].astype(str) + " " +  po_df['No Commande'].astype(str)).tolist()
    
    layout = [
    [sg.Text("Select all wanted orders from the dropown")],
    [sg.Combo(po_list, key='-DROPDOWN-', default_value = po_list[0], enable_events=True)],
    [sg.Button("Add")], 
    [sg.Listbox(values=selected_orders, size=(50, 10), key='-CHOSEN-', select_mode='multiple', enable_events=True)],
    [sg.Button("Remove"), sg.Button("Exit")]
]
    window = sg.Window("LabelEdge Optimiser", layout, size=(800, 600), resizable=True)

    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break
        
        if event == 'Add':
            addOrder(window, values['-DROPDOWN-'], selected_orders)
            
        if event == 'Remove':
            removeOrder(window, values['-CHOSEN-'], selected_orders)
                
    window.close()
  
# Add order from dropdown to list box  
def addOrder(window, selected_option, selected_orders):
    if selected_option not in selected_orders:
        selected_orders.append(selected_option)
        window['-CHOSEN-'].update(selected_orders)
        
        
# Remove selected orders from list box  
def removeOrder(window, items_to_delete, selected_orders):
    if items_to_delete:  # Check if an item is selected
        for item in items_to_delete:
            if item in selected_orders:
                selected_orders.remove(item)  # Remove the item from the list
        window['-CHOSEN-'].update(selected_orders)