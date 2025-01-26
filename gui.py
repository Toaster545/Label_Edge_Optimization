# import PySimpleGUI as sg

from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QComboBox
import sys

def createGui(po_df):
# create the gui for the application start

    # Step 1: Define a Main Window Class
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("LabelEdge Optimisor")
            self.setGeometry(100, 100, 600, 400)  # Set x, y, width, height
            self.initUI()

        def initUI(self):
            self.setWindowTitle("Dropdown Menu Example")
            self.setGeometry(100, 100, 300, 200)

            # Create a layout
            layout = QVBoxLayout()

            # Create a label to display the selected option
            self.label = QLabel("Select an option", self)

            # Create a combo box (dropdown)
            self.combo_box = QComboBox(self)
            
            # Add items to the combo box
            self.combo_box.addItem("Option 1")
            self.combo_box.addItem("Option 2")
            self.combo_box.addItem("Option 3")
            self.combo_box.addItem("Option 4")
            
            # Connect the signal to handle the selection change
            self.combo_box.currentTextChanged.connect(self.on_item_selected)

            # Add the combo box and label to the layout
            layout.addWidget(self.combo_box)
            layout.addWidget(self.label)

            # Set the layout for the main window
            self.setLayout(layout)

        def on_item_selected(self, text):
            # Update the label when an item is selected
            self.label.setText(f"Selected: {text}")  # Add a label to the window

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