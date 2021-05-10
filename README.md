# ZeroBT
This is a Python 3.x library to connect to a  Zero electric motorcycle via a Bluetooth and retrieve information.

## Why?
Because I wanted to write an Android app to display a "range" circle on Google Maps.

Because I wanted to monitor the charging remotely. The Bluetooth range is only about 20 feet maximum, so I set up a Raspberry Pi in range to talk to the bike and serve a web page.

Most importantly of all: THE ZERO ANDROID APP DOESN'T WORK

The Android app can't find the motorcycle and connect to it, even after you pair with it.

Yes, you pay $20,000 for an electric motorcycle, and you can't get a working app to connect to it and set up various modes. Seriously.

There's a workaround where you can install a 1.x version of the app, connect, and then upgrade, but you have to find an older version of the app somewhere on the net.

### Packets Supported

* BtSt - Battery Status
* DSt1 - Dash Status 1
* DSt2 - Dash Status 2
* DSt3 - Dash Status 3
* Gbki - Bike Info
* MbbR - Bike Board Read
* PwPk - Power Pack

### Example Code
```
#! /usr/bin/env python3
# print all possible Zero motorcycle Bluetooth packets

import zerobt

socket=zerobt.connect_to_bike()

print('Name:', zerobt.name)
print('Addr:', zerobt.addr)
print('Port:', zerobt.port)
print()

for cmd in sorted(zerobt.cmd_packets):
    packet=zerobt.read_packet(socket, cmd)
    print(cmd)
    for key in sorted(packet):
        print(key+':', packet[key])
    print()

socket.close()
```

Output:
```
Name: ZeroMotorcycles17210
Addr: 00:06:66:1C:BA:7A
Port: 1

BtSt
avg_pwr_over_dist_kw_mile: 0
battery_charge_critical_low: False
battery_charge_low: False
battery_out_of_balance: False
battery_temp_cold: False
battery_temp_critical_high: False
battery_temp_high: False
bike_on: True
charge_pct: 41
charger_0_attached: True
charger_1_attached: False
...
```
