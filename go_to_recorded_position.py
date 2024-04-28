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

# URI to the Crazyflie to connect to
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

MAX_VELOCITY = 0.25
SLEEP_TIME = 3

cflib.crtp.init_drivers()

 
class DroneMovement(threading.Thread):
    def __init__(self):
        super(DroneMovement, self).__init__()
        
        # array of saved positions for each board tile
        self.recorded_positions_xy = [None]

        # current drone position from lighthouse
        self.x_position
        self.y_position
        self.z_position
        self.set_velocity = 0.25

        # saved target position index
        self.target_pos_index = 0

        self.target_pos_threshold = 0.2

        self.if_run = False

    # default function that starts when the thread is started
    def run(self):

        # infinite loop for control
        while True:

            # check if drone released for movement
            if self.if_run:

                # connect to drone
                with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
                    # start position commander
                    with PositionHlCommander(self.scf, controller=PositionHlCommander.CONTROLLER_PID) as pc:

                        # control loop for drone movement
                        while self.if_run:
                            # make drone move (x, y, z, velocity)
                            pc.go_to(self.x_position, self.y_position, self.z_position, self.set_velocity)
                            # delay to let drone move
                            time.sleep(0.5)

                        # when drone no longer running, land the drone


                break

            # small time delay
            time.sleep(0.5)


    # function to check if drone reached setpoint
    def target_reached(self) -> bool:
        # check if drone within tolerance to setpoint
        if (abs(self.x_position - self.drone_board[self.target_pos_index].first) < self.target_pos_threshold) and (abs(self.y_position - self.drone_board[self.target_pos_index].second) < self.target_pos_threshold):
            return True
        else:
            return False

    # function for recording position of drone for corresponding board tile
    def record_tile_position(self, index) -> None:

        # connect to drone
        with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
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

    # function for choosing drone movement target
    def set_drone_tile_target(self, index) -> None:
        # update target index for use in run() function
        self.target_pos_index = index

    # function to start drone movement connection
    def start_drone(self) -> None:
        self.if_run = True

    # function to stop the drone movement
    def stop_drone(self) -> None:
        self.if_run = False


# main program
if __name__ == '__main__':

    # create drone thread
    drone_thread = DroneMovement()
    drone_thread.name = "thread_thread_name"
    drone_thread.daemon = True
    drone_thread.start()