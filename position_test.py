# Default libraries
import time
import os

# Local Classes
import drone

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

# URI to the Crazyflie to connect to
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

if __name__ == '__main__':
    cflib.crtp.init_drivers()

    drone_thread = drone.drone_thread_class()
    drone_thread.name = "drone_thread"
    drone_thread.daemon = True
    runstate = False
    runstate = input()
    if runstate == 1:
        drone_thread.start()
    else:
        quit

    index = 1

    while index != 0:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Please select an index to set: ")
        try:
            index = int(input())
            if index < 0 or index > 9:
                raise ValueError #this will send it to the print message and back to the input option
            break
        except:
            print("Not a valid option!")
            time.sleep(1)
        
        drone_thread.set_position(index)