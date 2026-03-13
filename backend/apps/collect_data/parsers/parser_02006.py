# -*- coding: utf-8 -*-
from ..utils import date_format, bytes_to_iridiumid


def parse_02006_type_0200601(data: bytes):
    iridiumid = bytes_to_iridiumid(data[10:25])
    sn = int.from_bytes(data[25:28], byteorder='big')

    data_real = data[51:]
    year = data_real[12]
    month = data_real[13]
    day = data_real[14]
    hour = data_real[15]
    minute = data_real[16]
    second = data_real[17]
    time = date_format(year, month, day, hour, minute, second)

    lonflag = -1
    if data_real[18] == 0x45:
        lonflag = 0
    elif data_real[18] == 0x57:
        lonflag = 1
    lon = int.from_bytes(data_real[19:23], byteorder='big') * 0.0000001

    latflag = -1
    if data_real[23] == 0x4E:
        latflag = 0
    elif data_real[23] == 0x53:
        latflag = 1
    lat = int.from_bytes(data_real[24:28], byteorder='big') * 0.0000001

    board_voltage = int.from_bytes(data_real[28:30], byteorder='big') * 0.001
    board_temp = int.from_bytes(data_real[30:32], byteorder='big', signed=True) * 0.01

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
    }
