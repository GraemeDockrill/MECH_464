# MECH 464 Tic Tac Toe Drone Project
# Authors: Graeme Dockrill

import tkinter as tk
import serial
from serial.tools import list_ports
import time
import struct

class TicTacToeUI:
    def __init__(self, master):
        self.master = master

        # Define serial port, baud rate, and packet size
        self.serial_port_option = "COM6"
        self.baud_rate = "9600"
        self.packet_size = 4

        # Define states
        self.COM_connected = False

        # Define some variables
        self.num_rows = 6
        self.num_columns = 3

        # Tic Tac Toe Variables
        self.played = set()    # A set to keep track of the played cells
        self.board = [' '] * 9 # A list of 9 strings, one for each cell, 
                  # will contain ' ' or 'X' or 'O'

        # Create UI for game
        self.create_ui()

    # Creates UI for Tic Tac Toe
    def create_ui(self):
        # Create Tic Tac Toe board buttons
        self.btn_board_1 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(1))
        self.btn_board_1.grid(row=3, column=0, sticky="nsew")
        self.btn_board_2 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(2))
        self.btn_board_2.grid(row=3, column=1, sticky="nsew")
        self.btn_board_3 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(3))
        self.btn_board_3.grid(row=3, column=2, sticky="nsew")
        self.btn_board_4 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(4))
        self.btn_board_4.grid(row=4, column=0, sticky="nsew")
        self.btn_board_5 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(5))
        self.btn_board_5.grid(row=4, column=1, sticky="nsew")
        self.btn_board_6 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(6))
        self.btn_board_6.grid(row=4, column=2, sticky="nsew")
        self.btn_board_7 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(7))
        self.btn_board_7.grid(row=5, column=0, sticky="nsew")
        self.btn_board_8 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(8))
        self.btn_board_8.grid(row=5, column=1, sticky="nsew")
        self.btn_board_9 = tk.Button(self.master, text="-", bg="grey", command=lambda: self.btn_board_click(9))
        self.btn_board_9.grid(row=5, column=2, sticky="nsew")

        # Create label for game
        self.lbl_title = tk.Label(self.master, text="Drone Tic Tac Toe")
        self.lbl_title.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Create COM connect button
        self.btn_connect = tk.Button(root, text="Connect", command=self.btn_connect_click)
        self.btn_connect.grid(row=2, column=0, columnspan=3, sticky="nsew")

        # Create COM Port drop down
        self.selected_port = tk.StringVar()
        self.selected_port.set("Select a COM Port")
        self.port_dropdown = tk.OptionMenu(root, self.selected_port, "")
        self.port_dropdown.grid(row=1, column=0, sticky="nsew", columnspan=3)
        self.refresh_ports()
        self.selected_port.trace_add('write', self.on_port_selected)

        # Set weight of rows and columns when resized
        for i in range(self.num_rows):
            root.grid_rowconfigure(i, weight=1)
        for i in range(self.num_columns):
            root.grid_columnconfigure(i, weight=1)

    # Function to handle valid button press
    def btn_board_click(self, clicked_button) -> None:

        # Check  which button was clicked and change it's color accordingly
        if clicked_button == 1:
            self.btn_board_1.configure(bg="red", state="disabled")
        if clicked_button == 2:
            self.btn_board_2.configure(bg="red", state="disabled")
        if clicked_button == 3:
            self.btn_board_3.configure(bg="red", state="disabled")
        if clicked_button == 4:
            self.btn_board_4.configure(bg="red", state="disabled")
        if clicked_button == 5:
            self.btn_board_5.configure(bg="red", state="disabled")
        if clicked_button == 6:
            self.btn_board_6.configure(bg="red", state="disabled")
        if clicked_button == 7:
            self.btn_board_7.configure(bg="red", state="disabled")
        if clicked_button == 8:
            self.btn_board_8.configure(bg="red", state="disabled")
        if clicked_button == 9:
            self.btn_board_9.configure(bg="red", state="disabled")

    # Refreshes available COM ports
    def refresh_ports(self, event=None):
        # Get a list of available COM ports
        ports = [port.device for port in list_ports.comports()]
        # Update the dropdown menu with the new ports
        self.port_dropdown['menu'].delete(0, 'end')
        for port in ports:
            self.port_dropdown['menu'].add_command(label=port, command=tk._setit(self.selected_port, port))

    # When connect button clicked
    def btn_connect_click(self):
        # First check if we're already connected
        if self.COM_connected:
            try:
                self.serial_port_thread.close()
                self.btn_connect.config(text="Connect")
                self.COM_connected = False
                self.serial_port.close()
            except Exception as e:
                print("Error closing serial port!")
                print(e)
        # Else we will try to connect
        else:
            try:
                self.serial_port_option = self.selected_port.get()
                self.serial_port = serial.Serial(self.serial_port_option, self.baud_rate)
                # time.sleep(0.1)
                if self.serial_port_thread.isOpen():
                    self.btn_connect.config(text="Disconnect")
                    self.COM_connected = True
            except Exception as e:
                print("Error opening serial port!")
                print(e)

    # Returns if port is open
    def isOpen(self):
        return self.serial_port.is_open
    
    # Writing to serial port
    def write_to_serial(self, COM_message):
        if self.isOpen:
            try:
                print("Wrote " + str(COM_message) + " to serial port!")
                self.serial_port.write(COM_message)     # Write byte array to serial
            except Exception as e:
                print("Error writing to serial port!")
                print(e)

    # Event on port being selected
    def on_port_selected(self, *args):
        print("Selected port:", self.selected_port.get())

    # Function to create byte packet with 1 start, 1 command, 4 data, 1 esc
    def create_message(self, command, data1, data2) -> bytearray:
        try:
            start_byte = 255
            start_byte = struct.pack('B', start_byte)       # Convert int into byte
            
            command_byte = struct.pack('B', command)       # Convert int into byte

            if data1 >= 65535:
                data1 = 65535
            data1_bytes = struct.pack('>H', data1)        # Pack into byte
            data1_bytes = bytearray(data1_bytes)

            if data2 >= 65535:
                data2 = 65535
            data2_bytes = struct.pack('>H', data2)        # Pack into byte
            data2_bytes = bytearray(data2_bytes)

            # Handle if escape byte is necessary
            esc_byte = 0

            if data1_bytes[0] >= 255:
                data1_bytes[0] = 0
                print("data1[0] >= 255")
                esc_byte |= 1 << 3
            if data1_bytes[1] >= 255:
                data1_bytes[1] = 0
                print("data1[1] >= 255")
                esc_byte |= 1 << 2
            if data2_bytes[0] >= 255:
                data2_bytes[0] = 0
                print("data2[0] >= 255")
                esc_byte |= 1 << 1
            if data2_bytes[1] >= 255:
                data2_bytes[1] = 0
                print("data2[1] >= 255")
                esc_byte |= 1 << 0

            print("Parsed message as: 255, " + str(command) + ", " + str(data1) + ", " + str(data2) + ", " + str(esc_byte))

            esc_byte = struct.pack('B', esc_byte)

            message = start_byte + command_byte + data1_bytes + data2_bytes + esc_byte

            return message
        except Exception as e:
            print("Problem creating message!")
            print(e)

    # Function run when window closed
    def close_program(self):
        self.master.destroy()


if __name__ == "__main__":

    # Initialize tkinter root
    root = tk.Tk()
    root.title("MECH 464 Drone Tic Tac Toe")

    # Create app
    app = TicTacToeUI(root)

    # Handle closing the window
    root.protocol("WM_DELETE_WINDOW", app.close_program)
    root.mainloop()
