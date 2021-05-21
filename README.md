# ZeroBT
This is a Python 3.x library to connect to a Zero electric motorcycle via
Bluetooth and retrieve information.

## Why?
Because I wanted to write an Android app to display a "range" circle on Google
Maps.

Because I wanted to monitor the charging remotely. The Bluetooth range is only
about 20 feet maximum, so I set up a Raspberry Pi in range to talk to the bike
and serve a web page.

Most importantly of all: THE ZERO ANDROID APP DOESN'T WORK

The Android app can't find the motorcycle and connect to it, even after you
pair with it.

Yes, you pay $20,000 for an electric motorcycle, and you can't get a working
app to connect to it and set up the custom mode. Seriously.

There's a workaround where you can install a 1.x version of the app, connect,
and then upgrade, but you have to find an older version of the app somewhere
on the net and hope it doesn't have malware in it.

### Installation

Place zerobt.py somewhere on the Python path like
/usr/lib/python3/dist-packages (Debian/Raspberry Pi OS)

### Packets Supported

* BtSt - Battery status
* DSt1 - Dash status 1
* DSt2 - Dash status 2
* DSt3 - Dash status 3
* Gbki - General bike info
* MbbR - Main Bike Board info
* PwPk - Power pack information

For details of what each packet contains, you can either run the example code,
or look at the source.

Note that the API determines the bike's model year by looking at the Main Bike
Board part number. Request a "Gbki" packet and use the "mbb_partno" field as a key
to the "mbb_model" dictionary.

### Example Code
```
#! /usr/bin/env python3
# print all possible Zero motorcycle Bluetooth packets

import zerobt

socket=zerobt.connect_to_bike()

try:
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
finally:
    socket.close()
```

Note the try..finally to ensure the socket is closed. The motorcycle supports
only one connection at a time, so if you don't close the socket, you have to
wait for a long timeout or turn the bike off before you can connect again.

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

### More Example Code
charging_data - Script that retrieves information as the bike is charging, and
outputs it in a CSV format suitable for a spreadsheet.

charging_status - Short sweet charging status script for the command line.

record_ride - Record a ride with the Raspberry Pi in a saddlebag.

extract_ride - Extract data suitable for a spreadsheet from data file produced
by above.

record_ride_gps - Record a ride with the Raspberry Pi and a GPS in a
saddlebag. You can use your phone as a GPS - read the script header for
details.

extract_ride_gps - Extract data suitable for Google Maps/Google Earth from
data file produced by above.

all_zero_packets - List all possible packets in an easy-to-read format.

all_zero_packets.txt - Example of above.

all_zero_packets_demo - List all possible packets as Python data items,
suitable for pasting into test code.

all_zero_packets_demo.txt - Example of above.

### Pairing the bike

You have to Bluetooth-pair the bike to whatever device you're using. If you're
using a Raspberry Pi, then you can perform the following procedure:

Pair with bike:
* Put the kickstand down.
* Turn off the kill switch.
* Hold down the mode button.
* Turn on the bike.
* Wait until the Bluetooth icon flashes. (about 5-10 seconds)
* Release mode button.

Run "bluetoothctl" and enter the following commands:

[bluetooth]# ```discoverable on```\
Changing discoverable on succeeded\
[CHG] Controller B8:27:EB:C4:1E:75 Discoverable: yes\
[bluetooth]# ```pairable on```\
Changing pairable on succeeded\
[bluetooth]# ```agent on```\
Agent is already registered\
[bluetooth]# ```default-agent```\
Default agent request successful\
[bluetooth]# ```scan on```\
Discovery started\
[CHG] Controller B8:27:EB:C4:1E:75 Discovering: yes\
Wait until you see something like:\
  [NEW] Device 00:06:66:1C:BA:7A ZeroMotorcycles17210\
Tell it to pair using the bike's address:\
[bluetooth]# ```pair 00:06:66:1C:BA:7A```\
Attempting to pair with 00:06:66:1C:BA:7A\
[CHG] Device 00:06:66:1C:BA:7A Connected: yes\
Request confirmation\
[agent] Confirm passkey 359602 (yes/no): ```yes```\
[CHG] Device 00:06:66:1C:BA:7A UUIDs: 00000000-deca-fade-deca-deafdecacaff\
[CHG] Device 00:06:66:1C:BA:7A UUIDs: 00001101-0000-1000-8000-00805f9b34fb\
[CHG] Device 00:06:66:1C:BA:7A ServicesResolved: yes\
[CHG] Device 00:06:66:1C:BA:7A Paired: yes\
Pairing successful\
Make it permanent across reboots:\
[bluetooth]# ```trust 00:06:66:1C:BA:7A```\
[CHG] Device 00:06:66:1C:BA:7A Trusted: yes\
Changing 00:06:66:1C:BA:7A trust succeeded\
Turn off discoverability and exit:\
[bluetooth]# ```discoverable off```\
Changing discoverable off succeeded\
[bluetooth]# ```quit```

Now you can turn the bike off.

### Uses
If you're using a Raspberry Pi with built-in Bluetooth and WiFi like a
Raspberry Pi 3 Model B, then it's robust enough to throw in a saddlebag and
power it from a USB charger in the cigarette lighter plug.

If you follow the instructions for "Raspberry Pi - Auto WiFi Hotspot Switch -
Direct Connection"
https://www.raspberryconnect.com/projects/65-raspberrypi-hotspot-accesspoints/158-raspberry-pi-auto-wifi-hotspot-switch-direct-connection
then you can access your Pi on the road from an SSH app like ConnectBot or a
laptop, and your Pi still reconnects to your home WiFi when you ride home, and
you can connect from your desktop.

This opens up a world of writing scripts to record your rides. The
"record_ride" and "extract_ride" scripts are a good starting point. The
advantage of saving the entire stream of packets is that later you can pick
and choose what data to extract.

Since the bike's Bluetooth range is so short, I designed a system to show the
bike's info on webpages, so you can monitor it as it charges.
