import sys
import random
import socket, threading, queue
import time
import re
from PySide6 import QtCore, QtWidgets

from PySide6.QtCore import Qt, QRunnable, QThreadPool, QTimer, Slot, QRect, Signal, QObject, QIODevice
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QFrame, QWidget, QTextEdit


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elevator Server App")


        self.button = QtWidgets.QPushButton("Show Command")
        self.button.clicked.connect(self.magic)
        self.text = QtWidgets.QLabel("Python Server App ", alignment=QtCore.Qt.AlignCenter)
        self.command_list = QtWidgets.QLabel("Next Command Coming Up: ", alignment=QtCore.Qt.AlignCenter)
        self.command_list.setFont(QFont("Arial", 20))
        self.command_list.hide()
        self.display = QTextEdit()
        self.display.setReadOnly(True)
        self.display.setFixedWidth(400)
        self.display.hide()


        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        self.text2 = QtWidgets.QLabel(f"Server IP address: {IPAddr}", alignment=QtCore.Qt.AlignCenter)


        self.button_2 = QtWidgets.QPushButton("Connect to serial port")
        self.button_2.clicked.connect(self.Button_2_action)
        self.button_2.clicked.connect(self.ConnectPort)
        self.text_message = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.text_from_STM = QtWidgets.QLabel(alignment=QtCore.Qt.AlignCenter)
        self.text_message.setFont(QFont("Arial", 14))
        self.text_from_STM.setFont(QFont("Arial", 14))
        self.message = ""

        # --- Configuration ---
        self.ELEVATOR_HEIGHT = 50
        self.ELEVATOR_WIDTH = 80
        self.SHAFT_HEIGHT = 450
        self.MOVE_SPEED = 20  # Pixels per timer step
        self.TIMER_INTERVAL = 50 # ms (controls frame rate of movement)

        # Define floor positions (Y-coordinates). Top (Floor 3) to Bottom (Floor 1).
        # Note: In Qt, Y=0 is the top edge.
        self.FLOOR_POSITIONS = {
            3: 50,  # Top floor (e.g., Y=50)
            2: 200, # Middle floor
            1: 350  # Bottom floor (e.g., Y=350)
        }
        
        self.current_floor = 1
        self.target_y = self.FLOOR_POSITIONS[self.current_floor]

        # --- GUI Setup ---
        central_widget = QWidget()
        
        # 1. Elevator Shaft (The main vertical container)
        self.shaft_frame = QFrame(central_widget)
        self.shaft_frame.setFrameShape(QFrame.Shape.Box)
        self.shaft_frame.setFrameShadow(QFrame.Shadow.Sunken)
        self.shaft_frame.setFixedHeight(self.SHAFT_HEIGHT)
        self.shaft_frame.setMinimumWidth(150)
        
        # 2. Elevator Cab (The moving widget)
        self.cab_widget = QtWidgets.QLabel("ELEVATOR")
        self.cab_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cab_widget.setStyleSheet("background-color: darkred; color: white; border: 2px solid gray;")
        self.cab_widget.setGeometry(
            QRect(150, self.target_y, self.ELEVATOR_WIDTH, self.ELEVATOR_HEIGHT) # Initial X, Y, Width, Height
        )
        # Parent the cab to the shaft so coordinates are relative to the shaft
        self.cab_widget.setParent(self.shaft_frame) 
        
        # 3. Control Panel and Status
        self.status_label = QtWidgets.QLabel(f"Current Floor: {self.current_floor}")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Arial", 20))
        
        self.move_button = QtWidgets.QPushButton("Move Up to Floor 3")
        self.move_button.clicked.connect(self.request_move)
        #self.move_button.clicked.connect(self.request_move2)
        
        # --- Movement Timer Setup ---
        self.move_timer = QTimer(self)
        self.move_timer.setInterval(self.TIMER_INTERVAL)
        self.move_timer.timeout.connect(self.update_elevator_position)

        # 1. Setup the Serial Port object
        self.serial = QSerialPort()
        
        # Important: Connect the readyRead signal to our handler
        self.serial.readyRead.connect(self.receive_data)

        ################################################
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Create a horizontal layout
        self.elevator_section_layout = QtWidgets.QHBoxLayout()

        # Add status label and command list to the inside-vertical layout
        self.status_and_command_layout = QtWidgets.QVBoxLayout()
        self.status_and_command_layout.addStretch(1)
        self.status_and_command_layout.addWidget(self.status_label)
        self.status_and_command_layout.addStretch(1)
        self.status_and_command_layout.addWidget(self.command_list)
        self.status_and_command_layout.addWidget(self.display)
        self.status_and_command_layout.addStretch(5)

        # Add elevator components to the inside-vertical layout
        self.shaft_and_controls_layout = QtWidgets.QVBoxLayout()
        self.shaft_and_controls_layout.addWidget(self.shaft_frame) # The main visual component
        self.shaft_and_controls_layout.addWidget(self.move_button)
        self.shaft_and_controls_layout.addStretch(1) # Add stretch to push controls to the top/center

        self.elevator_section_layout.addLayout(self.status_and_command_layout)
        self.elevator_section_layout.addLayout(self.shaft_and_controls_layout)

        self.layout.addStretch(1)
        self.layout.addWidget(self.text)
        self.layout.addStretch(1)
        self.layout.addWidget(self.text2)
        self.layout.addStretch(1)

        self.layout.addLayout(self.elevator_section_layout)

        self.layout.addStretch(5)
        self.layout.addWidget(self.text_message)
        self.layout.addWidget(self.text_from_STM)
        self.layout.addStretch(5)  
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.button_2)
        
        self.setLayout(self.layout)
#############################################################################
    @QtCore.Slot()
    def magic(self):
        if self.command_list.isVisible():
            # If it's visible, hide it and change button text to show
            self.command_list.hide()
            self.display.hide()
            self.button.setText("Show Command")
        else:
            # If it's hidden, show it and change button text to hide
            self.command_list.show()
            self.display.show()
            self.button.setText("Hide Command")
    
    @QtCore.Slot()
    def Button_2_action(self):
        self.text_message.setText( f"Connecting...")
        self.button_2.setEnabled(False)
        self.button_2.setText("Connecting...")
        app.processEvents()  # forces the GUI to update


    def extract_command(self, text):
        try:
            a, b, c = map(float, text.strip().split(','))
        except ValueError:
            self.text.setText("Invalid data")
            return None

        print(a, b, c)

        # Example usage

        command = ""
        if a>= b and a>=c:
            command = 'K'
        elif b>=c:
            command = 'L'
        else:
            command = 'O'
    
        print(command)

        return command
    
    @Slot(int) # Expects the integer interval from the signal
    def start_main_timer_safely(self, interval):
        """Safely starts the QTimer on the main GUI thread."""
        self.move_timer.setInterval(interval)
        self.move_timer.start()

    def move(self, command):

        next_floor = self.current_floor

        # K = move to the 3rd floor
        if command == 'K':
            next_floor = 3
            self.status_label.setText(f"Moving to Floor: {next_floor}")
                
        # L = move to the 1st floor
        elif command == 'L':
            next_floor = 1
            self.status_label.setText(f"Moving to Floor: {next_floor}")

        # O = open the door
        elif command == 'O':
            self.open_door_sequence()
            # We return here because the sequence will handle re-enabling the button
            return

        elif command == '\0':
            pass
            
        self.target_y = self.FLOOR_POSITIONS[next_floor]
        self.current_floor = next_floor

        self.move_button.setDisabled(True)
    
        # Start the movement timer
        self.move_timer.start()


    def ConnectPort(self):
        # 2. Configure Port Settings
        # Replace 'COM3' or '/dev/ttyACM0' with your STM32's port
        self.serial.setPortName("COM6") 
        self.serial.setBaudRate(QSerialPort.Baud115200)
        self.serial.setDataBits(QSerialPort.Data8)
        self.serial.setParity(QSerialPort.NoParity)
        self.serial.setStopBits(QSerialPort.OneStop)
        self.serial.setFlowControl(QSerialPort.NoFlowControl)

        if self.serial.open(QIODevice.ReadWrite):
            self.display.append("--- Port Opened Successfully ---\n")
            self.text_message.setText("Connected")
            print("serial port connected")
        else:
            self.display.append(f"--- Error: {self.serial.errorString()} ---")
            self.text_message.setText("Error")

        app.processEvents()  # forces the GUI to update

    def receive_data(self):
        # 3. Read the data
        # readAll() returns a QByteArray
        message=""
        while self.serial.canReadLine():
            data = self.serial.readLine()
            print("data received")
        
            # Convert bytes to string (handling potential decoding errors)
            message = data.data().decode('utf-8').strip('\n')
        
            # Display the message
            self.display.insertPlainText(message)
        
             # Auto-scroll to bottom
        self.display.ensureCursorVisible()

        command = self.extract_command(message)
        self.move(command)
    
    def request_move(self):
        """Determines the next target floor and starts the timer."""
        # Simple logic: Toggle between Floor 1 and Floor 3
        if self.current_floor == 1:
            next_floor = 3
        else:
            next_floor = 1
            
        self.target_y = self.FLOOR_POSITIONS[next_floor]
        self.current_floor = next_floor
        
        self.status_label.setText(f"Moving to Floor: {self.current_floor}")
        self.move_button.setDisabled(True)
        
        # Start the movement timer
        self.move_timer.start()

    def request_move2(self):
        command = 'O'
        self.move(command)
    
    def update_elevator_position(self):
        """Called by QTimer to move the elevator cab one step."""
        current_y = self.cab_widget.y()
        
        if current_y == self.target_y:
            # Movement complete
            self.move_timer.stop()
            self.status_label.setText(f"Arrived at Floor: {self.current_floor}")
            self.move_button.setText(f"Move {'Down' if self.current_floor == 3 else 'Up'} to Floor {'1' if self.current_floor == 3 else '3'}")
            self.move_button.setDisabled(False)
            return
            
        # Determine direction and step size
        if current_y < self.target_y:
            # Moving Down (Y increases)
            step = self.MOVE_SPEED
        else:
            # Moving Up (Y decreases)
            step = -self.MOVE_SPEED
            
        # Calculate next position, ensuring we don't overshoot the target
        new_y = current_y + step
        
        # Correct for overshoot on the final step
        if (step > 0 and new_y > self.target_y) or (step < 0 and new_y < self.target_y):
            new_y = self.target_y
            
        # Update the cab's position using move()
        self.cab_widget.move(self.cab_widget.x(), new_y)
    
    def open_door_sequence(self):
        """
        Step 1: Start the Door Opening phase.
        """
        self.move_button.setDisabled(True) # Disable button while busy
        self.status_label.setText("Door Opening")
        
        # Use QTimer.singleShot to schedule the next step (close_door_sequence) 
        # to run after 2000 milliseconds (2 seconds).
        QTimer.singleShot(2000, self.close_door_sequence)

    def close_door_sequence(self):
        """
        Step 2: Start the Door Closing phase.
        """
        self.status_label.setText("Door Closing")
        
        # Use QTimer.singleShot to schedule the final step (finish_door_sequence) 
        QTimer.singleShot(2000, self.finish_door_sequence)

    def finish_door_sequence(self):
        """
        Step 3: Finish the sequence and update the status.
        """
        self.status_label.setText(f"Currently at Floor: {self.current_floor}")
        self.move_button.setDisabled(False) # Re-enable the button




if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    # gives the control to the app
    app.exec()

    # terminates the program successfully
    sys.exit(0)


