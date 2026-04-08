# -*- coding: utf-8 -*-
from ..utils import date_format, bytes_to_iridiumid


def parse_02007_type_0200701(data: bytes):
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
    if data_real[10] == 0x45:
        lonflag = 0
    elif data_real[10] == 0x57:
        lonflag = 1
    lon = int.from_bytes(data_real[11:15], byteorder='big') * 0.0000001

    latflag = -1
    if data_real[15] == 0x4E:
        latflag = 0
    elif data_real[15] == 0x53:
        latflag = 1
    lat = int.from_bytes(data_real[16:20], byteorder='big') * 0.0000001

    board_voltage = int.from_bytes(data_real[20:22], byteorder='big') * 0.001
    board_temp = int.from_bytes(data_real[22:24], byteorder='big', signed=True) * 0.01

    temps_40 = []
    for i in range(40):
        start = 24 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps_40.append(str(t))

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
        'tempC40': ','.join(temps_40),
    }
