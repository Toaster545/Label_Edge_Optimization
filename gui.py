import PySimpleGUI as sg

from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QComboBox
import sys

def createGui(po_df):
# create the gui for the application start

    selected_items = []
    
    layout = [
    [sg.Text("Select an option from the dropdown:")],
    [sg.Combo(['Option 1', 'Option 2', 'Option 3'], default_value='Option 1', key='-DROPDOWN-', enable_events=True)],
    [sg.Button("Add")], 
    [sg.Listbox(values=selected_items, size=(30, 6), key='-LISTBOX-')],
    [sg.Button("Exit")]
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
    window.close()