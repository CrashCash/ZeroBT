"""Communicate with Zero Motorcycles over Bluetooth."""

# Place in /usr/lib/python3/dist-packages on Debian

import bluetooth
import pydbus
import select
import struct
import time
import zlib

# info of last device we looked at
name=None
addr=None
port=None

# standard Bluetooth Serial Port Profile (SPP) UUID
uuid='00001101-0000-1000-8000-00805F9B34FB'

# precomputed command packets
cmd_packets={'BtSt':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00BtSt\xf8\xf4\xf2\xf1\xe2\xef\xc0\xf9', # Battery Status
             'DSt1':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00DSt1\xf8\xf4\xf2\xf1\xc0\x03\x0f\xbf', # Dash Status 1
             'DSt2':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00DSt2\xf8\xf4\xf2\xf1\x10y\xaf\xf8',    # Dash Status 2
             'DSt3':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00DSt3\xf8\xf4\xf2\xf1\xa0P\xcf\xc5',    # Dash Status 3
             'Gbki':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00Gbki\xf8\xf4\xf2\xf1\x81\x9ew\xc5',    # Bike Info
             'MbbR':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00MbbR\xf8\xf4\xf2\xf1\x16ZI\xa5',       # Bike Board Read
             'PwPk':b'\xf1\xf2\xf4\xf8\x00\x00\x00\x00PwPk\xf8\xf4\xf2\xf1\xd4\xb1\x92\x92'} # Power Pack

header=b'\xF1\xF2\xF4\xF8\x00\x00\x00\x00'
trailer=b'\xF8\xF4\xF2\xF1'

# map of MBB part number to model year
# This is the "mbb_partno" from the "Gbki" packet
mbb_model={'41-05027' :'2013',
           '41-06288' :'2014',
           '41-07782' :'2015',
           '41-07782A':'2016',
           '40-08064' :'2017',
           '40-08084' :'2017',
           '40-08064A':'2018',
           '40-08084A':'2018',
           '40-08064B':'2019',
           '40-08084B':'2019',
           '40-08064C':'2020',
           '40-08084C':'2020',
           '40-08064D':'2021',
           '40-08084D':'2021',
           '40-08064E':'2022',
           '40-08084E':'2022'}

class Error(Exception):
    """Internal: Base class for exceptions in this module."""
    pass

class NoData(Error):
    """Raised when no data received from bike."""
    pass

class NoDevices(Error):
    """Raised when no data received from bike."""
    pass

class NoServices(Error):
    """Raised when no services are discovered for a bike."""
    pass

def _null_terminated(offset):
    """Internal: Grab null-terminated data from bytes."""
    end=data.find(0, offset)
    return data[offset:end].decode('ascii')

def _ubyte(offset):
    """Internal: Extract an unsigned byte."""
    return data[offset]

def _ushort(offset):
    """Internal: Extract a 2-byte unsigned short."""
    return struct.unpack('<H', data[offset:offset+2])[0]

def _sshort(offset):
    """Internal: Extract a 2-byte signed short."""
    return struct.unpack('<h', data[offset:offset+2])[0]

def _uint(offset):
    """Internal: Extract a 4-byte unsigned integer."""
    return struct.unpack('<I', data[offset:offset+4])[0]

def _compute_checksum(packet):
    """Compute Reversed CRC-32 packet checksum.

    See:
        https://www.scadacore.com/tools/programming-calculators/online-checksum-calculator/
        http://www.sunshine2k.de/coding/javascript/crc/crc_js.html
        https://en.wikipedia.org/wiki/Cyclic_redundancy_check
    """
    # compute checksum
    cksum=zlib.crc32(packet)
    # convert to bytes
    cksum=cksum.to_bytes(4, byteorder='big')
    # reverse the order of bytes
    return cksum[::-1]

def _compute_cmd_packet(cmd):
    """Compute a command packet from a 4-character command string.

    Command structure:
    Header (constant): F1F2F4F8 00000000
    4-byte command: 5077506B (PwPk)
    Trailer (constant): F8F4F2F1
    Reversed CRC-32 checksum: D4B19292
    """
    cmd_pkt=header+bytearray(cmd, 'ascii')+trailer
    cmd_pkt+=compute_checksum(cmd_pkt)
    return cmd_pkt

# yes, this is a really bullshit way to do this, but it works and I haven't found the real way to do it
def _get_paired_devices_linux():
    """Internal: Return list of paired Bluetooth devices on Linux."""
    bus_tag='org.bluez'
    device_tag=bus_tag+'.Device1'
    bus=pydbus.SystemBus()
    manager=bus.get(bus_tag, '/')
    objs=manager.GetManagedObjects()
    return [objs[x][device_tag] for x in objs if device_tag in objs[x]]

# sorry
def _get_paired_devices_windows():
    raise NotImplementedError('Cannot find paired devices on Windows')

def get_motorcycle_devices():
    """Return list of Zero motorcycle devices."""
    devices=[]
    for entry in _get_paired_devices_linux():
        if entry['Name'].startswith('ZeroMotorcycles'):
            devices.append(entry)
    if not devices:
        raise NoDevices('No paired motorcycle devices found')
    return devices

def get_addr(substr=None):
    """Return address of bike with specific substring, or just the first one."""
    global name, addr, port
    devices=get_motorcycle_devices()
    if not substr:
        name=devices[0]['Name']
        addr=devices[0]['Address']
        return addr
    for device in devices:
        if substr in device['Name']:
            name=device['Name']
            addr=device['Address']
            return addr
    raise NoDevices('No paired motorcycle devices found with "'+substr+'" in the name')

def get_services(address=None, retries=1, callback=None):
    """Discover Bluetooth services at address. This looks for it on the air.

    retries  -- retry count
    callback -- called after each failure
    """
    global name, addr, port
    addr=address
    if not addr:
        addr=get_addr()
    tries=0
    while (retries):
        services=bluetooth.find_service(uuid=uuid, address=addr)
        if services:
            if tries:
                # prevent "Connection reset by peer" error
                # don't jump on it the moment it comes on the air
                time.sleep(5)
            return services
        if callback:
            callback()
        retries-=1
        tries+=1
    raise NoServices('No Bluetooth services found at '+addr)

def get_port(address, retries=1, callback=None):
    """Return port serviced by bike at address.

    retries  -- retry count
    callback -- called after each failure
    """
    global name, addr, port
    addr=address
    port=get_services(addr, retries, callback)[0]['port']
    return port

def get_addr_and_port(substr=None, retries=1, callback=None):
    """Return address and port of bike. Can restrict to bike with substring in name.

    retries  -- retry count
    callback -- called after each failure
    """
    global name, addr, port
    addr=get_addr(substr)
    port=get_port(addr, retries, callback)
    return addr, port

def connect(addr, port):
    """Connect to address and port and return open Bluetooth socket.

    addr -- Bluetooth address
    port -- Bluetooth service port

    You are responsible for closing this socket after use.
    Since the bike only accepts one connection, not closing the socket will block other connections
    until it times out or the bike is turned off.
    """
    sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((addr, port))
    return sock

def connect_to_bike(substr=None, retries=1, callback=None):
    """I don't care about addresses and ports, I want a socket connected to a bike.

    retries  -- retry count
    callback -- called after each failure

    You are responsible for closing this socket after use.
    Since the bike only accepts one connection, not closing the socket will block other connections
    until it times out or the bike is turned off.
    """
    global name, addr, port
    addr, port=get_addr_and_port(substr, retries, callback)
    return connect(addr, port)

def read_packet(sock, cmd, timeout=0.5):
    """Send command to bike, read data, and return decoded packet.

    sock    -- Bluetooth socket
    cmd     -- 4-character command
    timeout -- time to wait for end of packet with select()

    Decoded packet is a dictionary with descriptive keys.
    """
    global data

    if timeout <= 0:
        raise ValueError('Timeout must be greater than zero')

    if cmd not in cmd_packets:
        raise ValueError('Invalid command')

    # 3 strikes, you're out
    tries=3
    complete=False
    while not complete and tries:
        tries-=1
        # use precomputed packet
        cmd_pkt=cmd_packets[cmd]
        sock.send(cmd_pkt)

        # read data
        data=b''
        while not complete and select.select([sock], [], [], timeout)[0]:
            data+=sock.recv(1024)
            i=data.find(trailer)
            size=len(data)
            complete=(i > 0) and (size-i == 8)

    # squawk if we didn't get anything
    if not data or not complete:
        raise NoData('No data received')

    # check checksum
    cs=_compute_checksum(data[:-4])
    if cs != data[-4:]:
        raise NoData('bad checksum')

    #print(data)

    # decode data
    data_type=data[8:12].decode('ascii')
    packet={'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'type': data_type}
    if data_type == 'Gbki':
        # General bike info packet
        packet['vin']=_null_terminated(12)
        packet['make']=_null_terminated(30)
        packet['model']=_null_terminated(50)
        packet['mbb_partno']=_null_terminated(82)
        packet['bms_partno']='' # not done
        packet['mbb_fw_ver']=_uint(108)
        packet['bms_fw_ver']=_uint(112)
    elif data_type == 'BtSt':
        # Battery status packet
        packet['pack_voltage_mv']=_uint(12)
        packet['pack_capacity_ah']=_ushort(16)
        packet['pack_capacity_remain_ah']=_ushort(18)
        packet['charge_pct']=_ubyte(20)
        packet['pack_temp_c']=[]
        for i in range(8):
            packet['pack_temp_c'].append(_sshort(22+i*2))
        flags=_uint(40)
        packet['battery_out_of_balance']     =(flags & 0x100000)>0
        packet['battery_charge_critical_low']=(flags & 0x200000)>0
        packet['battery_charge_low']         =(flags & 0x400000)>0
        packet['battery_temp_cold']          =(flags & 0x800000)>0
        packet['battery_temp_critical_high'] =(flags & 0x1000000)>0
        packet['battery_temp_high']          =(flags & 0x2000000)>0
        packet['bike_on']                    =(flags & 0x4000000)>0
        packet['charger_1_attached']         =(flags & 0x8000000)>0
        packet['charger_0_attached']         =(flags & 0x10000000)>0
        packet['odometer_miles']=_uint(44)
        packet['avg_pwr_over_dist_kw_mile']=_ushort(48) # not done
        packet['total_power_used_kw']=_uint(52)
    elif data_type == 'MbbR':
        # Main bike board read packet
        packet['motor_torque_nm']=_sshort(12)
        packet['motor_speed_rpm']=_ushort(14)
        packet['motor_temp_c']=_ushort(16)
        packet['controller_temp_c']=_ushort(18)
        packet['battery_current_amps']=_sshort(20)
        packet['motor_current_amps']=_ushort(22)
        packet['bike_speed_mph']=_ushort(24)
        flags=_uint(28)
        packet['charging']       =(flags & 0x200000)>0
        packet['brake_applied']  =(flags & 0x1000000)>0
        packet['temp_warning']   =(flags & 0x2000000)>0
        packet['bike_armed']     =(flags & 0x4000000)>0
        packet['killswitch_stop']=(flags & 0x8000000)>0
        packet['kickstand_down'] =(flags & 0x10000000)>0
        packet['max_custom_speed_mph']=_ushort(32)
        packet['max_custom_torque_pct']=_ushort(34)
        packet['max_custom_regen_torque_pct']=_ushort(36)
        packet['max_custom_brake_regen_torque_pct']=_ushort(38)
    elif data_type == 'PwPk':
        # Power pack packet
        packet['pack_voltage_mv']=_uint(12)
        cells=[]
        packet['cell_voltage_mv']=[]
        for i in range(28):
            packet['cell_voltage_mv'].append(_ushort(16+i*2))
        packet['cell_voltage_min_mv']=min(packet['cell_voltage_mv'])
        packet['cell_voltage_max_mv']=max(packet['cell_voltage_mv'])
        packet['charge_pct']=_ubyte(72)
        packet['pack_capacity_ah']=_ushort(74)
        packet['pack_capacity_remain_ah']=_ushort(76)
        packet['pack_temp_c']=[]
        for i in range(8):
            packet['pack_temp_c'].append(_sshort(78+i*2))
        packet['pack_temp_max_c']=_sshort(94)
        packet['pack_temp_min_c']=_sshort(96)
        packet['motor_temp_c']=_sshort(98)
        packet['motor_temp_max_c']=_sshort(100)
        packet['controller_temp_c']=_sshort(102)
        packet['battery_current_amps']=_sshort(104)
        packet['motor_current_amps']=_sshort(106)
        packet['num_charge_cycles']=_uint(108)
    elif data_type == 'DSt1':
        # Dash status 1 packet
        packet['trip_1_km']=_uint(12)/100
        packet['motor_rpm']=_ushort(16)
        packet['error_code']=_ushort(18)
    elif data_type == 'DSt2':
        # Dash status 2 packet
        packet['trip_2_km']=_uint(12)/100
        packet['est_range_km']=_ushort(16)/100
        packet['motor_temp_c']=_ushort(18)
    elif data_type == 'DSt3':
        # Dash status 3 packet
        packet['minutes_until_charged']=_ushort(12)
        packet['wh_per_km_instant']=_uint(14)/100
        packet['wh_per_km_avg']=_ushort(20)/100
        packet['wh_per_km_life']=_ushort(22)/100
    elif data_type == 'ReSd':
        # Resend packet
        return read_packet(sock, cmd, timeout)
    else:
        print(data)
        raise ValueError('Unknown packet type: "'+data_type+'" size: '+str(len(data)))

    return packet
