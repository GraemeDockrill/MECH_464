# Default libraries
import time
import logging
import os

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

import threading

class DroneMovement(threading.Thread):
    def __init__(self):
        super(DroneMovement, self).__init__()

        cflib.crtp.init_drivers()

        # URI to the Crazyflie to connect to
        self.uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

        self.MAX_VELOCITY = 0.25
        self.SLEEP_TIME = 3
        
        # array of saved positions for each board tile
        self.recorded_positions_xy = [(None, None)] * 9

        # current drone position from lighthouse
        self.x_current_position = 0
        self.y_current_position = 0

        # Velocity and Position Constants
        self.z_target_position = 0.15
        self.set_velocity = 0.10

        # saved target position index
        self.target_pos_index = 0

        self.target_pos_threshold = 0.2

        self.if_run = False

    # default function that starts when the thread is started
    def run(self):

        # infinite loop for control
        while True:
            print("On-standby")
            # check if drone released for movement
            if self.if_run:
                print("Running")

                try:
                    # connect to drone
                    with SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache')) as scf:

                        print("Connected to drone")
                        # start position commander
                        with PositionHlCommander(scf , controller=PositionHlCommander.CONTROLLER_PID) as pc:
                            print("HL commander started")

                            time.sleep(1)

                            # initialize log configuration
                            log_config = LogConfig(name='State Estimate', period_in_ms=250)
                            log_config.add_variable('stateEstimate.x', 'float')
                            log_config.add_variable('stateEstimate.y', 'float')
                            log_config.add_variable('stateEstimate.z', 'float')


                            # start reading drone memory for lighthouse position
                            with SyncLogger(scf, log_config) as logger:

                                print("Started SyncLogger")
                                
                                # control loop for drone movement
                                while self.if_run:
                                    print("Checked for running...")

                                    # get current drone position for comparison
                                    # reading through drone data
                                    for log_entry in logger:
                                        data = log_entry[1]

                                        # print('[%d][%s]: %s' % (timestamp, logconf_name, data))

                                        # add recorded x,y position to array
                                        self.x_current_position = data['stateEstimate.x']
                                        self.y_current_position = data['stateEstimate.y']

                                        [x, y] = self.recorded_positions_xy[self.target_pos_index]
                                        print(str(self.x_current_position) + ", " + str(self.y_current_position))
                                        print(str(x) + ", " + str(y))

                                        break

                                    #logger.next()

                                    # make drone move (x, y, z, velocity)
                                    [x, y] = self.recorded_positions_xy[self.target_pos_index]
                                    pc.go_to(x, y, self.z_target_position, self.set_velocity)
                                    # delay to let drone move
                                    time.sleep(1)

                                # when drone no longer running, land the drone
                                pc.land()

                    print("Exiting")

                    break
                except Exception as e:
                    print(e)

            # small time delay
            time.sleep(2)


    # function to check if drone reached setpoint
    def target_reached(self) -> bool:
        # check if drone within tolerance to setpoint
        for x_target, y_target in self.drone_board[self.target_pos_index]:
            if (abs(self.x_current_position - x_target) < self.target_pos_threshold) and (abs(self.y_current_position - y_target) < self.target_pos_threshold):
                return True
            else:
                return False

    # function for recording position of drone for corresponding board tile
    def record_tile_position(self, index) -> None:

        # connect to drone
        with SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache')) as scf:
            # initialize log configuration
            log_config = LogConfig(name='State Estimate', period_in_ms=250)
            log_config.add_variable('stateEstimate.x', 'float')
            log_config.add_variable('stateEstimate.y', 'float')
            log_config.add_variable('stateEstimate.z', 'float')

            # read from drone memory
            with SyncLogger(scf, log_config) as logger:
                # reading through drone data
                for log_entry in logger:
                    timestamp = log_entry[0]
                    data = log_entry[1]
                    logconf_name = log_entry[2]

                    print('[%d][%s]: %s' % (timestamp, logconf_name, data))

                    # add recorded x,y position to array
                    self.recorded_positions_xy[index] = (data['stateEstimate.x'], data['stateEstimate.y'])

                    break

        return

    # function for choosing drone movement target
    def set_drone_tile_target(self, index) -> None:
        # update target index for use in run() function
        self.target_pos_index = index

    # debugging function to print recorded drone positions
    def print_recorded_positions_xy(self) -> None:
        print(self.recorded_positions_xy)

    # function to start drone movement connection
    def start_drone(self) -> None:
        self.if_run = True

    # function to stop the drone movement0
    
    def stop_drone(self) -> None:
        self.if_run = False


# main program
if __name__ == '__main__':

    default_index_set = {0,1,2,3,4,5,6,7,8}

    # create drone thread
    drone_thread = DroneMovement()
    drone_thread.name = "thread_thread_name"
    # drone_thread.daemon = True
    drone_thread.start()

    # loop for all tiles
    while len(default_index_set) > 0:
        # continuously prompt user for input
        while True:
            print("Please select an index to set: ")
            print(default_index_set)
            try:
                index = int(input())
                if index < 0 or index > 8:
                    raise ValueError #this will send it to the print message and back to the input option
                if index not in default_index_set:
                    raise ValueError
                break
            except:
                print("Not a valid option!")
                time.sleep(0.25)
            print("")

        default_index_set.remove(index)
        # record current drone position
        drone_thread.record_tile_position(index)

    # print the calibration positions
    drone_thread.print_recorded_positions_xy()
    
    # start drone
    print("Drone Take-off")
    drone_thread.start_drone()
    time.sleep(5)

    # move to tile 1
    print("Move to tile 1")
    drone_thread.set_drone_tile_target(1)
    time.sleep(10)

    #while not drone_thread.target_reached():
    #    time.sleep(0.25) 

    # move to tile 2
    print("Move to tile 2")
    drone_thread.set_drone_tile_target(2)
    time.sleep(10)

    # move to tile 3
    print("Move to tile 3")
    drone_thread.set_drone_tile_target(3)
    time.sleep(10)

    # stop drone
    drone_thread.stop_drone()
    print("Stopped Succesfully!")