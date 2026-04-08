# -*- coding: utf-8 -*-
from ..utils import date_format, bytes_to_iridiumid


def parse_02003_type_0200301(data: bytes):
    iridiumid = bytes_to_iridiumid(data[10:25])
    sn = int.from_bytes(data[25:28], byteorder='big')

    data_real = data[51:]
    year = data_real[3]
    month = data_real[4]
    day = data_real[5]
    hour = data_real[6]
    minute = data_real[7]
    second = data_real[8]
    time = date_format(year, month, day, hour, minute, second)

    lonflag = -1
    if data_real[9] == 0x45:
        lonflag = 0
    elif data_real[9] == 0x57:
        lonflag = 1
    lon = int.from_bytes(data_real[10:14], byteorder='big') * 0.0000001

    latflag = -1
    if data_real[14] == 0x4E:
        latflag = 0
    elif data_real[14] == 0x53:
        latflag = 1
    lat = int.from_bytes(data_real[15:19], byteorder='big') * 0.0000001

    board_voltage = int.from_bytes(data_real[19:21], byteorder='big') * 0.001
    board_temp = int.from_bytes(data_real[21:23], byteorder='big', signed=True) * 0.01
    acpdu_status = data_real[23]
    acpdu_voltage = int.from_bytes(data_real[24:26], byteorder='big') * 0.1
    acpdu_current = int.from_bytes(data_real[26:28], byteorder='big') * 0.001
    solar_radiation = int.from_bytes(data_real[28:30], byteorder='big')
    solar_batt_voltage = int.from_bytes(data_real[30:32], byteorder='big') * 0.1
    solar_voltage = int.from_bytes(data_real[32:34], byteorder='big') * 0.1
    solar_charge_current = int.from_bytes(data_real[34:36], byteorder='big') * 0.1
    batt_capacity = int.from_bytes(data_real[36:38], byteorder='big') * 0.1
    solar_generation = int.from_bytes(data_real[38:40], byteorder='big')
    ctrl_temp = int.from_bytes(data_real[40:42], byteorder='big') * 0.01
    voltage = int.from_bytes(data_real[42:46], byteorder='big') * 0.0001
    current = int.from_bytes(data_real[46:50], byteorder='big') * 0.0001
    power = int.from_bytes(data_real[50:54], byteorder='big') * 0.0001
    dcpdu_status = data_real[54]
    dcpdu_voltage = int.from_bytes(data_real[55:57], byteorder='big') * 0.1
    dcpdu_current = int.from_bytes(data_real[57:59], byteorder='big') * 0.001
    cabin_temp = int.from_bytes(data_real[59:61], byteorder='big') * 0.1
    cabin_humid = int.from_bytes(data_real[61:63], byteorder='big') * 0.1
    wind_batt_voltage = int.from_bytes(data_real[63:65], byteorder='big') * 0.1
    wind_charge_current = int.from_bytes(data_real[65:67], byteorder='big') * 0.1
    wind_voltage = int.from_bytes(data_real[67:69], byteorder='big') * 0.1
    wind_current = int.from_bytes(data_real[69:71], byteorder='big') * 0.1
    wind_instant_power = int.from_bytes(data_real[71:73], byteorder='big') * 0.1
    wind_total_generation = int.from_bytes(data_real[73:75], byteorder='big') * 0.1
    wind_rotatespeed = int.from_bytes(data_real[75:77], byteorder='big') * 0.1
    wind_status = int.from_bytes(data_real[77:79], byteorder='big')

    atmosphere = float(data_real[79:85].decode('utf-8', errors='ignore').strip() or 0)
    air_temp = float(data_real[85:91].decode('utf-8', errors='ignore').strip() or 0)
    wind_direct = float(data_real[91:96].decode('utf-8', errors='ignore').strip() or 0)
    wind_speed = float(data_real[96:101].decode('utf-8', errors='ignore').strip() or 0)

    temps_pt = []
    for i in range(4):
        start = 101 + i * 4
        t = int.from_bytes(data_real[start:start + 4], byteorder='big', signed=True)
        temps_pt.append(str(t))

    temps_bio = []
    for i in range(10):
        start = 117 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps_bio.append(str(t))

    return {
        'iridiumid': iridiumid,
        'sn': sn,
        'time': time,
        'latflag': latflag,
        'lat': lat,
        'lonflag': lonflag,
        'lon': lon,
        'board_voltage': board_voltage,
        'board_temp': board_temp,
        'acpdu_status': acpdu_status,
        'acpdu_voltage': acpdu_voltage,
        'acpdu_current': acpdu_current,
        'solar_radiation': solar_radiation,
        'solar_batt_voltage': solar_batt_voltage,
        'solar_voltage': solar_voltage,
        'solar_charge_current': solar_charge_current,
        'batt_capacity': batt_capacity,
        'solar_generation': solar_generation,
        'ctrl_temp': ctrl_temp,
        'voltage': voltage,
        'current': current,
        'power': power,
        'dcpdu_status': dcpdu_status,
        'dcpdu_voltage': dcpdu_voltage,
        'dcpdu_current': dcpdu_current,
        'cabin_temp': cabin_temp,
        'cabin_humid': cabin_humid,
        'wind_batt_voltage': wind_batt_voltage,
        'wind_charge_current': wind_charge_current,
        'wind_voltage': wind_voltage,
        'wind_current': wind_current,
        'wind_instant_power': wind_instant_power,
        'wind_total_generation': wind_total_generation,
        'wind_rotatespeed': wind_rotatespeed,
        'wind_status': wind_status,
        'atmosphere': atmosphere,
        'air_temp': air_temp,
        'wind_direct': wind_direct,
        'wind_speed': wind_speed,
        'tempC_pt': ','.join(temps_pt),
        'tempC_bio': ','.join(temps_bio),
    }
