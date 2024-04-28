# default Python libraries
import os
import time
import threading
import csv

# cfclient libraries
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

Z_HEIGHT = 0.15

class drone_thread_class(threading.Thread):
    def __init__(self):
        super(drone_thread_class, self).__init__()
        self.data = [None]

        try:
            # Initialize the low-level drivers (don't list the debug drivers)
            cflib.crtp.init_drivers(enable_debug_driver=False)
            self.uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
            self.scf = SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache'))
            self.pc = PositionHlCommander(self.scf, controller=PositionHlCommander.CONTROLLER_PID)

            with SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache')) as self.scf:
                with PositionHlCommander(self.scf, controller=PositionHlCommander.CONTROLLER_PID) as self.pc:
                    self.init_drone_board()
        except:
            print("Failed to connect to CrazyFlie")

    def run(self):
         with SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                with PositionHlCommander(self.scf, controller=PositionHlCommander.CONTROLLER_PID) as pc:
                    pc.go_to(self.x_position, self.y_position, self.z_position)
                    time.sleep(0.5)
            
    def init_drone_board(self):
        default_index_set = {1,2,3,4,5,6,7,8,9}
        self.drone_board = [None] * 9

        while len(default_index_set):
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Please select an index to set: ")
                print(default_index_set)
                try:
                    index = int(input())
                    if index < 1 or index > 9:
                        raise ValueError #this will send it to the print message and back to the input option
                    if index not in default_index_set:
                        raise ValueError
                    break
                except:
                    print("Not a valid option!")
                    time.sleep(1)

            # Add the current position of the drone into the index of the 
            default_index_set.remove(index)
            [self.x_position, self.y_position, self.z_position] = self.pc.get_position()
            self.z_position = Z_HEIGHT
            self.drone_board[index - 1] = (self.x_position, self.y_position)

        self.x_position = 0
        self.y_position = 0
        self.z_position = 0

    def log_position(self) -> None:
        cf = self.scf.cf
        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')

        log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
        log_config.add_variable('kalman.varPX', 'float')
        log_config.add_variable('kalman.varPY', 'float')
        log_config.add_variable('kalman.varPZ', 'float')

        with SyncLogger(self,log_config) as logger:
            for log_entry in logger:
                self.data.append(log_entry[1])

    def export_position_log(self, file_name) -> bool:
        with open(file_name, 'w', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in self.data:
                filewriter.writerow(row)

    def export_drone_board(self, file_name) -> bool:
        with open(file_name, 'w', newline='') as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for index in range(10):
                filewriter.writerow(self.drone_board[index])

    # Function to move the drone to an index 
    def set_position(self, index) -> None:
        self.x_position = self.drone_board[index].first
        self.y_position = self.drone_board[index].second
        self.z_position = Z_HEIGHT

    def return_reached_position(self, index):
        threshold = 0.05
        [self.x_position, self.y_position, self.z_position] = self.pc.get_position()

        if (abs(self.x_position - self.drone_board[index].first) < threshold) and (abs(self.y_position - self.drone_board[index].second) < threshold):
            return True
        else:
            return False

    def close_drone(self) -> None:
            self.cf.close_link()