import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.position_hl_commander import PositionHlCommander
from cflib.utils import uri_helper

# URI to the Crazyflie to connect to
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

def matrix_print(cf, pc):

    pc.go_to(0,0.1,0.15)
    time.sleep(1)
    pc.go_to(0,0.2,0.15)
    time.sleep(3)
    pc.go_to(0,0.1,0.15)


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Synced with drone")
        with PositionHlCommander(scf, default_height=0.5, controller=PositionHlCommander.CONTROLLER_PID) as pc:
            print("Configured Position Commander")
            pc.go_to(0,0.1,0.15)
            time.sleep(3)
            