# -*- coding: utf-8 -*-
from ..utils import date_format, bytes_to_iridiumid


def _parse_03003_common(data: bytes):
    iridiumid = bytes_to_iridiumid(data[10:25])
    sn = int.from_bytes(data[25:28], byteorder='big')

    data_real = data[51:]
    year = data_real[4]
    month = data_real[5]
    day = data_real[6]
    hour = data_real[7]
    minute = data_real[8]
    second = data_real[9]
    time = date_format(year, month, day, hour, minute, second)

    lonflag = -1
    if data_real[11] == 0x45:
        lonflag = 0
    elif data_real[11] == 0x57:
        lonflag = 1
    lon = int.from_bytes(data_real[12:16], byteorder='big') * 0.0000001

    latflag = -1
    if data_real[16] == 0x4E:
        latflag = 0
    elif data_real[16] == 0x53:
        latflag = 1
    lat = int.from_bytes(data_real[17:21], byteorder='big') * 0.0000001

    board_voltage = int.from_bytes(data_real[21:23], byteorder='big') * 0.001

    return {
        'iridiumid': iridiumid,
        'sn': sn,
        'time': time,
        'latflag': latflag,
        'lat': lat,
        'lonflag': lonflag,
        'lon': lon,
        'board_voltage': board_voltage,
    }


def parse_03003_type_301_part1(data: bytes):
    d = _parse_03003_common(data)
    data_real = data[51:]

    d['sonar_on'] = int.from_bytes(data_real[23:25], byteorder='big') * 0.001
    d['sonar_under'] = int.from_bytes(data_real[25:28], byteorder='big') * 0.001
    d['ST_temp'] = round(int.from_bytes(data_real[28:32], byteorder='big', signed=True) * 0.0001, 4)
    d['CTD_c2'] = round(int.from_bytes(data_real[32:34], byteorder='big') * 0.0001, 4)
    d['CTD_t2'] = round(int.from_bytes(data_real[34:38], byteorder='big', signed=True) * 0.0001, 4)
    d['CTD_v2'] = round(int.from_bytes(data_real[38:42], byteorder='big') * 0.0001, 4)

    ctds_bytes = bytes([0x00, data[42], data[43], data[44]])
    d['CTD_s2'] = round(int.from_bytes(ctds_bytes, byteorder='big', signed=True) * 0.0001, 4)
    d['CTD_d2'] = round(int.from_bytes(data[45:49], byteorder='big') * 0.0001, 4)

    d['air_humid'] = round(int.from_bytes(data_real[49:51], byteorder='big') * 0.1, 1)
    d['air_temp'] = round(int.from_bytes(data_real[51:53], byteorder='big', signed=True) * 0.1, 1)
    d['atmosphere'] = int.from_bytes(data_real[53:55], byteorder='big') * 0.1
    return d


def parse_03003_type_301_part2(data: bytes):
    d = _parse_03003_common(data)
    data_real = data[51:]

    temps = []
    for i in range(150):
        start = 23 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))

    d['tempC150'] = ','.join(temps)
    return d
