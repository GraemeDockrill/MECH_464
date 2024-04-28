# default Python libraries
import os
import time

# cfclient libraries
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

class drone:
    def __init__(self, master):
         self.drone_board = [None] * 9

    def init_drone(self) -> None:
        # Initialize the low-level drivers (don't list the debug drivers)
        cflib.crtp.init_drivers(enable_debug_driver=False)
        self.uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

        self.scf = SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache'))
        self.pc = PositionHlCommander(self.scf, default_height=0.5, controller=PositionHlCommander.CONTROLLER_PID)

    def init_drone_board(self) -> None:
        default_index_set = {1,2,3,4,5,6,7,8,9}

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
            self.estimate_drone_position(self.scf)
            self.drone_board[index - 1] = (self.x_position, self.y_position)

    def get_URI_ports(self) -> None:
        cflib.crtp.init_drivers()
        available = cflib.crtp.scan_interfaces()
        for i in available:
            print ("Found Crazyflie on URI [%s] with comment [%s]" (available[0], available[1]))

    def estimate_drone_position(self) -> None:
        cf = self.scf.cf
        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')

        self.wait_for_estimate()

    def wait_for_estimate(self) -> None:
        log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
        log_config.add_variable('kalman.varPX', 'float')
        log_config.add_variable('kalman.varPY', 'float')
        log_config.add_variable('kalman.varPZ', 'float')

        with SyncLogger(self,log_config) as logger:
            for log_entry in logger:
                data = log_entry[1]

                self.x_position = data['kalman.varPX']
                self.y_position = data['kalman.varPY']
                self.z_position = data['kalman.varPZ']

    # Function to move the drone to an index 
    def go_to_position(self, index) -> None:
        x_position = self.drone_board[index].first
        y_position = self.drone_board[index].second
        z_position = 0.15
        self.pc.go_to(x_position, y_position, z_position)
        self.move_flag = True

    def return_reached_position(self):
        return [self.x_position, self.y_position]

    def close_drone(self) -> None:
            self.cf.close_link()