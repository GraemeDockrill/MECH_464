import cflib.crtp

# Initiate the low level drivers
cflib.crtp.init_drivers()

print('Scanning interfaces for Crazyflies...')

for a in range(100):
    available = cflib.crtp.scan_interfaces(0xe7e7e7e700 + a)
    print('Crazyflies found:')
    for i in available:
        print(i[0])