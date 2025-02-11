import PySimpleGUI as sg
import sys
from algos import solve, createProductBlocks

def createGui(po_df, inv_df):
# create the gui for the application start

    sg.theme('DarkBlue3')
    
    selected_orders = []
    products = []
    po_list = (po_df['No'].astype(str) + " " + po_df['Vendu à'].astype(str) + " " +  po_df['No Commande'].astype(str)).tolist()
    
    layout = [
    [sg.Button("Choose Orders", button_color=("black", "white"), size=(15, 2), border_width=10)]
    ]
    
    
    window = sg.Window("LabelEdge Optimiser", layout, size=(800, 600), resizable=True)

    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break
        
        if event == 'Choose Orders':
            temp = openOrders(inv_df, po_df, po_list)
            layout = temp[0]
            products = temp[1]
            window.close()
            window = sg.Window("LabelEdge Optimiser", layout, size=(800, 600), resizable=True)
            event, values = window.read()
            
        # useless functions for now
        if event == 'Add':
            addOrder(window, values['-DROPDOWN-'], selected_orders)
            
        if event == 'Remove':
            removeOrder(window, values['-CHOSEN-'], selected_orders)
        
        if event == "Submit":
            
            papers = inv_df['Code LabelEdge'].unique()
            selected_paper_key = next((key for key, val in values.items() if key.startswith("-PAPER_") and val), None)
            util_tol = float(values["-INPUT1-"])
            rem_tol = float(values["-INPUT2-"])

            # Extract the actual paper value using the index
            if selected_paper_key:
                selected_index = int(selected_paper_key.replace("-PAPER_", "").replace("-", ""))
                selected_paper_value = papers[selected_index]
            
            value = solve(inv_df=inv_df, 
                          po_df=po_df ,
                          selected_pos=[products[i] for i in range(len(products)) if values[f"-PROD_{i}-"]], 
                          label_code=selected_paper_value,
                          util_tol=util_tol, 
                          rem_tol=rem_tol
                          )
                
    window.close()


# Creat a window to selct orders from checkbox
def openOrders(inv_df, po_df, po_list):
    
    # setup the layout of the order window
    new_layout = [
        [sg.Text("Check all wanted orders", font=("Arial", 14, "bold"))],
        *[[sg.Checkbox(task, key=f"-ORDER_{i}-")] for i, task in enumerate(po_list)],  # Each checkbox is in its own list
        [sg.Button("Submit")]
    ]
    
    new_window = sg.Window("Order Selector", new_layout, size=(800, 600), resizable=True)
    
    # loop to keep the order window open
    while True:
        event, values = new_window.read()
        
        if event == sg.WINDOW_CLOSED or event == "Exit":
            break
        
        if event == 'Submit':
            checked_orders = [po_list[i] for i in range(len(po_list)) if values[f"-ORDER_{i}-"]]
            products = createProductBlocks(po_df, checked_orders)
            layout = updateBase(inv_df, products)
            break
        
    new_window.close()
    
    return [layout, products]
            
# Update the base with the selected orders
def updateBase(inv_df, products):
    papers = inv_df['Code LabelEdge'].unique()
    papers = sorted(inv_df['Code LabelEdge'].dropna().unique())
    
    layout = [
        [sg.Text("All orders to be processed")],
        [
            sg.Column(
                [[sg.Checkbox(task, key=f"-PROD_{i}-")] for i, task in enumerate(products)], 
                size=(200, 300), scrollable=True, vertical_scroll_only=True
            ),
            sg.VSeparator(),
            sg.Column(
                [[sg.Radio(task, "PAPER_GROUP", key=f"-PAPER_{i}-")] for i, task in enumerate(papers)], 
                size=(200, 300), scrollable=True, vertical_scroll_only=True
            )
        ],
        [
        sg.Text("Percentage of \"Full\" master roll:"), sg.InputText(default_text="0.8", key="-INPUT1-", size=(10, 1)),
        sg.Text("Max Removal Percentage :"), sg.InputText(default_text="0.1", key="-INPUT2-", size=(10, 1))
        ],
        [sg.Button("Remove"), sg.Button("Submit"), sg.Button("Exit")]
    ]
    
    return layout
    
def selectProducts(products, values):
    checked_products = [products[i] for i in range(len(products)) if values[f"-PROD_{i}-"]]

    return checked_products
                

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
