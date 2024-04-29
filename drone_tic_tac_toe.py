# MECH 464 Tic Tac Toe Drone Project
# Authors: Graeme Dockrill, Sam Bonnell (to a much lesser extent)

import tkinter as tk
import serial
from serial.tools import list_ports
import time
import struct
import random
import logging
import threading

# Local Classes
import drone
import go_to_recorded_position

# Crazyflie Libraries
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils.multiranger import Multiranger
from cflib.utils import uri_helper
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

logging.basicConfig(level=logging.ERROR)

class TicTacToeUI:
    def __init__(self, master):
        self.master = master

        # Define serial port, baud rate, and packet size
        self.serial_port_option = "COM6"
        self.baud_rate = "9600"
        self.packet_size = 4

        # Define states
        self.COM_connected = False
        self.drone_flying = False

        # Define some variables
        self.num_rows = 8
        self.num_columns = 3

        # Custom font
        self.custom_button_font = ("Helvetica", 50, "bold")
        self.custom_label_font = ("Helvetica", 30, "bold")

        # Tic Tac Toe Variables
        self.played = set()    # A set to keep track of the played cells
        self.board = [' '] * 9 # A list of 9 strings, one for each cell, 
                  # will contain ' ' or 'X' or 'O'
        self.game_end_blink_delay = 0.2
        self.game_end_blink_times = 4

        # Create UI for game
        self.create_ui()

        self.default_index_set = {0,1,2,3,4,5,6,7,8}

        self.drone_thread = go_to_recorded_position.DroneMovement()
        self.drone_thread.name = "drone_thread"
        self.drone_thread.start()

        # loop for all tiles
        while len(self.default_index_set) > 0:
            # continuously prompt user for input
            while True:
                print("Please select an index to set: ")
                print(self.default_index_set)
                try:
                    index = int(input())
                    if index < 0 or index > 8:
                        raise ValueError #this will send it to the print message and back to the input option
                    if index not in self.default_index_set:
                        raise ValueError
                    break
                except:
                    print("Not a valid option!")
                    time.sleep(0.25)
                print("")

            self.default_index_set.remove(index)
            # record current drone position
            self.drone_thread.record_tile_position(index)

    # Creates UI for Tic Tac Toe
    def create_ui(self):
        # Create Tic Tac Toe board buttons
        self.btn_board_0 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(0))
        self.btn_board_0.grid(row=4, column=0, sticky="nsew")
        self.btn_board_1 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(1))
        self.btn_board_1.grid(row=4, column=1, sticky="nsew")
        self.btn_board_2 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(2))
        self.btn_board_2.grid(row=4, column=2, sticky="nsew")
        self.btn_board_3 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(3))
        self.btn_board_3.grid(row=5, column=0, sticky="nsew")
        self.btn_board_4 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(4))
        self.btn_board_4.grid(row=5, column=1, sticky="nsew")
        self.btn_board_5 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(5))
        self.btn_board_5.grid(row=5, column=2, sticky="nsew")
        self.btn_board_6 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(6))
        self.btn_board_6.grid(row=6, column=0, sticky="nsew")
        self.btn_board_7 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(7))
        self.btn_board_7.grid(row=6, column=1, sticky="nsew")
        self.btn_board_8 = tk.Button(self.master, text="-", font=self.custom_button_font, command=lambda: self.btn_board_click(8))
        self.btn_board_8.grid(row=6, column=2, sticky="nsew")

        # Create button for restarting
        self.btn_restart_game = tk.Button(self.master, text="Restart Game", state="disabled", font=self.custom_label_font, command=lambda: self.restart_game())
        self.btn_restart_game.grid(row=7, column=0, columnspan=3, sticky="nsew")

        # Create label for game
        self.lbl_title = tk.Label(self.master, font=self.custom_button_font, text="Drone Tic Tac Toe")
        self.lbl_title.grid(row=0, column=0, columnspan=3, sticky="nsew")

        # Create label for game status
        self.lbl_game_state = tk.Label(self.master, font=self.custom_label_font, text="Make your move")
        self.lbl_game_state.grid(row=3, column=0, columnspan=3, sticky="nsew")

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

    # Function for restarting the game when it's complete
    def restart_game(self) -> None:

        # Clear the played set and reset the board
        self.played.clear()
        for i in range(9):
            self.board[i] = " "

        # Reset LEDs on board
        self.write_to_serial(9, 1)

        # Disable the restart button
        self.btn_restart_game.configure(state="disabled")

        # move drone to board center
        self.drone_thread.set_drone_tile_target(4)
        time.sleep(5)

        # Reenable board buttons
        self.btn_board_0.configure(text="-", state="active")
        self.btn_board_1.configure(text="-", state="active")
        self.btn_board_2.configure(text="-", state="active")
        self.btn_board_3.configure(text="-", state="active")
        self.btn_board_4.configure(text="-", state="active")
        self.btn_board_5.configure(text="-", state="active")
        self.btn_board_6.configure(text="-", state="active")
        self.btn_board_7.configure(text="-", state="active")
        self.btn_board_8.configure(text="-", state="active")

        self.lbl_game_state.configure(text="Make your move")

    # Function to handle player button press
    def btn_board_click(self, clicked_button) -> None:

        # Add clicked button to played list
        self.played.add(clicked_button)
        self.board[clicked_button] = "O"

        print(clicked_button)

        # Check  which button was clicked and change it's color accordingly
        if clicked_button == 0:
            self.btn_board_0.configure(text="O", state="disabled")
        if clicked_button == 1:
            self.btn_board_1.configure(text="O", state="disabled")
        if clicked_button == 2:
            self.btn_board_2.configure(text="O", state="disabled")
        if clicked_button == 3:
            self.btn_board_3.configure(text="O", state="disabled")
        if clicked_button == 4:
            self.btn_board_4.configure(text="O", state="disabled")
        if clicked_button == 5:
            self.btn_board_5.configure(text="O", state="disabled")
        if clicked_button == 6:
            self.btn_board_6.configure(text="O", state="disabled")
        if clicked_button == 7:
            self.btn_board_7.configure(text="O", state="disabled")
        if clicked_button == 8:
            self.btn_board_8.configure(text="O", state="disabled")

        # Handle 3 and 5 being switched on the board
        if (clicked_button == 3):
            clicked_button = 5
        elif (clicked_button == 5):
            clicked_button = 3

        # Activate LED on board
        self.write_to_serial(clicked_button, 0)

        # Check if player has won
        if self.terminate("O"):
            # Disable all buttons
            self.btn_board_0.configure(state="disabled")
            self.btn_board_1.configure(state="disabled")
            self.btn_board_2.configure(state="disabled")
            self.btn_board_3.configure(state="disabled")
            self.btn_board_4.configure(state="disabled")
            self.btn_board_5.configure(state="disabled")
            self.btn_board_6.configure(state="disabled")
            self.btn_board_7.configure(state="disabled")
            self.btn_board_8.configure(state="disabled")
            # Enable restart button
            self.btn_restart_game.configure(state="active")
            return

        # Call drone to make its move
        self.computerNextMove()

    # Function to handle the drone's move and to update the board when the drone move is done
    def computerNextMove(self) -> None:

        # on first boot up, take off with drone
        if not self.drone_flying:
            self.drone_flying = True
            self.drone_thread.start_drone()
            time.sleep(2)

        self.lbl_game_state.configure(text="Drone making a move")

        # Disable all buttons when this is happening
        self.btn_board_0.configure(state="disabled")
        self.btn_board_1.configure(state="disabled")
        self.btn_board_2.configure(state="disabled")
        self.btn_board_3.configure(state="disabled")
        self.btn_board_4.configure(state="disabled")
        self.btn_board_5.configure(state="disabled")
        self.btn_board_6.configure(state="disabled")
        self.btn_board_7.configure(state="disabled")
        self.btn_board_8.configure(state="disabled")


        computer_move = random.randint(0, 8) # generate computer move

        # if computer_move space is played, generate another
        while(computer_move in self.played):
            computer_move = random.randint(0, 8)

        print(computer_move)

        # Add drone move
        self.played.add(computer_move)
        self.board[computer_move] = "X"

        # When drove move is selected, make the move
        self.drone_thread.set_drone_tile_target(computer_move)
        time.sleep(5)

        # When drone reaches target, update buttons on board
        if computer_move == 0:
            self.btn_board_0.configure(text="X")
        if computer_move == 1:
            self.btn_board_1.configure(text="X")
        if computer_move == 2:
            self.btn_board_2.configure(text="X")
        if computer_move == 3:
            self.btn_board_3.configure(text="X")
        if computer_move == 4:
            self.btn_board_4.configure(text="X")
        if computer_move == 5:
            self.btn_board_5.configure(text="X")
        if computer_move == 6:
            self.btn_board_6.configure(text="X")
        if computer_move == 7:
            self.btn_board_7.configure(text="X")
        if computer_move == 8:
            self.btn_board_8.configure(text="X")

        # Handle 3 and 5 being switched on the board
        if (computer_move == 3):
            computer_move = 5
        elif (computer_move == 5):
            computer_move = 3

        # Activate LED on board
        self.write_to_serial(computer_move, 1)

        # Check if drone has won the game
        if self.terminate("X"):
            # Disable all buttons
            self.btn_board_0.configure(state="disabled")
            self.btn_board_1.configure(state="disabled")
            self.btn_board_2.configure(state="disabled")
            self.btn_board_3.configure(state="disabled")
            self.btn_board_4.configure(state="disabled")
            self.btn_board_5.configure(state="disabled")
            self.btn_board_6.configure(state="disabled")
            self.btn_board_7.configure(state="disabled")
            self.btn_board_8.configure(state="disabled")
            # Enable restart button
            self.btn_restart_game.configure(state="active")
            return


        # Otherwise reenable the available selected buttons
        if 0 not in self.played:
            self.btn_board_0.configure(state="active")
        if 1 not in self.played:
            self.btn_board_1.configure(state="active")
        if 2 not in self.played:
            self.btn_board_2.configure(state="active")
        if 3 not in self.played:
            self.btn_board_3.configure(state="active")
        if 4 not in self.played:
            self.btn_board_4.configure(state="active")
        if 5 not in self.played:
            self.btn_board_5.configure(state="active")
        if 6 not in self.played:
            self.btn_board_6.configure(state="active")
        if 7 not in self.played:
            self.btn_board_7.configure(state="active")
        if 8 not in self.played:
            self.btn_board_8.configure(state="active")

        self.lbl_game_state.configure(text="Make your move")

    # 
    def terminate(self, who: str) -> bool:
        """ returns True if who (being passed 'X' or 'O') has won or if it's a draw, False otherwise;
            it also prints the final messages:
                    "You won! Thanks for playing." or 
                    "You lost! Thanks for playing." or 
                    "A draw! Thanks for playing."  
        """

        # inner function to display text for winning or losing
        def printWinorLose(who: str):
            if(who == "O"):
                self.lbl_game_state.configure(text="You won! Thanks for playing.")
            else:
                self.lbl_game_state.configure(text="You lost! Thanks for playing.")

        # inner function to blink the LEDs
        def blink_leds(LED1, LED2, LED3, colour):
            for i in range(self.game_end_blink_times):
                    self.write_to_serial(9, 0)
                    time.sleep(self.game_end_blink_delay)
                    self.write_to_serial(LED1, colour)
                    self.write_to_serial(LED2, colour)
                    self.write_to_serial(LED3, colour)
                    time.sleep(self.game_end_blink_delay)
        
        # check all win cases, then print who won, else continue
        if(who == self.board[0] == self.board[1] == self.board[2]): # top row
            printWinorLose(who)
            if self.board[0] == "O":
                blink_leds(0, 1, 2, 0)
            elif self.board[0] == "X":
                blink_leds(0, 1, 2, 1)
            return True
        elif(who == self.board[3] == self.board[4] == self.board[5]): # middle row
            printWinorLose(who)
            if self.board[3] == "O":
                blink_leds(5, 4, 3, 0)
            elif self.board[3] == "X":
                blink_leds(5, 4, 3, 1)
            return True
        elif(who == self.board[6] == self.board[7] == self.board[8]): # bottom row
            printWinorLose(who)
            if self.board[6] == "O":
                blink_leds(6, 7, 8, 0)
            elif self.board[6] == "X":
                blink_leds(6, 7, 8, 1)
            return True
        elif(who == self.board[0] == self.board[3] == self.board[6]): # left column
            printWinorLose(who)
            if self.board[0] == "O":
                blink_leds(0, 5, 6, 0)
            elif self.board[0] == "X":
                blink_leds(0, 5, 6, 1)
            return True
        elif(who == self.board[1] == self.board[4] == self.board[7]): # middle column
            printWinorLose(who)
            if self.board[1] == "O":
                blink_leds(1, 4, 7, 0)
            elif self.board[1] == "X":
                blink_leds(1, 4, 7, 1)
            return True
        elif(who == self.board[2] == self.board[5] == self.board[8]): # right column
            printWinorLose(who)
            if self.board[2] == "O":
                blink_leds(2, 3, 8, 0)
            elif self.board[2] == "X":
                blink_leds(2, 3, 8, 1)
            return True
        elif(who == self.board[0] == self.board[4] == self.board[8]): # top left diagonal column
            printWinorLose(who)
            if self.board[0] == "O":
                blink_leds(0, 4, 8, 0)
            elif self.board[0] == "X":
                blink_leds(0, 4, 8, 1)
            return True
        elif(who == self.board[2] == self.board[4] == self.board[6]): # top right diagonal column
            printWinorLose(who)
            if self.board[2] == "O":
                blink_leds(2, 4, 6, 0)
            elif self.board[2] == "X":
                blink_leds(2, 4, 6, 1)
            return True
        elif(set([0,1,2,3,4,5,6,7,8]).issubset(self.played)): # board full
            self.lbl_game_state.configure(text="A draw! Thanks for playing.")
            return True
        else:
            return False

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
                time.sleep(0.1)
                if self.serial_port.is_open:
                    self.btn_connect.config(text="Disconnect")
                    self.COM_connected = True
                    # Reset LEDs on board
                    self.write_to_serial(9, 1)
            except Exception as e:
                print("Error opening serial port!")
                print(e)

    # Returns if port is open
    def isOpen(self):
        return self.serial_port.is_open
    
    # Writing to serial port
    def write_to_serial(self, square, colour):

        # First 4 bits are for the color
        COM_byte = 0b00000000
        COM_byte += square

        if colour == 0:
            COM_byte = COM_byte | 0b00000000
        else:
            COM_byte = COM_byte | 0b10000000


        if self.isOpen:
            try:
                # COM_byte = struct.pack('B', command)
                print("Wrote " + str(int.to_bytes(COM_byte, 1, "little")) + " to serial port!")
                self.serial_port.write(int.to_bytes(COM_byte, 1, "little"))     # Write byte array to serial
            except Exception as e:
                print("Error writing to serial port!")
                print(e)

    # Event on port being selected
    def on_port_selected(self, *args):
        print("Selected port:", self.selected_port.get())

    # Function run when window closed LAND DRONE
    def close_program(self):
        self.drone_thread.stop_drone()
        self.master.destroy()


if __name__ == "__main__":

    # Initialize tkinter root
    root = tk.Tk()
    root.title("MECH 464 Drone Tic Tac Toe")

    # Initialize playing positions


    # Create app
    app = TicTacToeUI(root)

    # Handle closing the window
    root.protocol("WM_DELETE_WINDOW", app.close_program)
    root.mainloop()