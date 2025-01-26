# import PySimpleGUI as sg

from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel
import sys

def createGui(po_df):
# create the gui for the application start

    # Step 1: Define a Main Window Class
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Start app")
            self.setGeometry(100, 100, 600, 400)  # Set x, y, width, height
            self.initUI()

        def initUI(self):
            label = QLabel("Hello, PyQt6!", self)  # Add a label to the window
            label.move(50, 50)  # Position the label at x=50, y=50

    # Step 2: Create the Application Instance
    app = QApplication(sys.argv)  # QApplication requires a list of command-line arguments

    # Step 3: Instantiate and Show the Main Window
    window = MainWindow()
    window.show()
    # Step 4: Run the Application's Event Loop
    app.exec()


'''
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
'''