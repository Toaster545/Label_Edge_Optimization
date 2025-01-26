import PySimpleGUI as sg

from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QComboBox
import sys

def createGui(po_df):
# create the gui for the application start


    layout = [
    [sg.Text("Select an option from the dropdown:")],
    [sg.Combo(['Option 1', 'Option 2', 'Option 3'], default_value='Option 1', key='-DROPDOWN-')],
    [sg.Button("Submit"), sg.Button("Exit")]
]
    window = sg.Window("Simple App", layout, size=(800, 600))

    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == "OK":
            break
    
    

    window.close()