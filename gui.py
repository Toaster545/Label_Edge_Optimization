import PySimpleGUI as sg
import sys
from algos import solve

def createGui(po_df, inv_df):
# create the gui for the application start

    sg.theme('DarkBlue3')
    
    selected_orders = []
    po_list = (po_df['No'].astype(str) + " " + po_df['Vendu à'].astype(str) + " " +  po_df['No Commande'].astype(str)).tolist()
    
    layout = [
    [sg.Button("Choose Orders", button_color=("white", "black"), size=(15, 2), border_width=10)]
    ]
    
    window = sg.Window("LabelEdge Optimiser", layout, size=(800, 600), resizable=True)

    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break
        
        if event == 'Choose Orders':
            layout = openOrders(po_list)
            window.close()
            window = sg.Window("LabelEdge Optimiser", layout, size=(800, 600), resizable=True)
            event, values = window.read()
            
        # useless functions for now
        if event == 'Add':
            addOrder(window, values['-DROPDOWN-'], selected_orders)
            
        if event == 'Remove':
            removeOrder(window, values['-CHOSEN-'], selected_orders)
        
        if event == "Submit":
            value = solve(inv_df=inv_df, po_df=po_df ,selected_pos=selected_items)
                
    window.close()


# Creat a window to selct orders from checkbox
def openOrders(po_list):
    
    # setup the layout of the order window
    new_layout = [
    [sg.Text("Check all wanted orders", font=("Arial", 14, "bold"))],
    [sg.Checkbox(po_list, key=f"-ORDER_{i}-") for i, task in enumerate(po_list)],
    [sg.Button("Submit")]
    ]
    
    new_window = sg.Window("Order Selector", new_layout, size=(800, 600), resizable=True)
    
    # loop to keep the order window open
    while True:
        event, values = new_window.read()
        
        if event == sg.WINDOW_CLOSED:
            break
        
        if event == 'Submit':
            checked_orders = [po_list[i] for i in range(len(po_list)) if values[f"-ORDER_{i}-"]]
            layout = updateBase(checked_orders)
            break
        
    new_window.close()
    
    return layout 
            
# Update the base with the selected orders
def updateBase(checked_orders):
    layout = [
    [sg.Text("All orders to be processed")], 
    [sg.Listbox(values=checked_orders, size=(50, len(checked_orders)), key='-CHOSEN-', select_mode='multiple', enable_events=True)],
    [sg.Button("Remove"), sg.Button("Exit")]
    ]
    
    return layout
    

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
