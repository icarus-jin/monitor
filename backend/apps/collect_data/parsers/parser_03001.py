# -*- coding: utf-8 -*-
from ..utils import date_format, bytes_to_iridiumid


def parse_03001_type_101(data: bytes):
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


def parse_03001_type_102(data: bytes):
    d = parse_03001_type_101(data)
    data_real = data[51:]
    d['atmosphere'] = int.from_bytes(data_real[24:27], byteorder='big') * 0.01
    return d


def parse_03001_type_103(data: bytes):
    d = parse_03001_type_101(data)
    data_real = data[51:]
    year = data_real[24]
    month = data_real[25]
    day = data_real[26]
    hour = data_real[27]
    minute = data_real[28]
    second = data_real[29]

    d['bd_time'] = date_format(year, month, day, hour, minute, second)
    d['bd_posflag'] = data_real[30]

    bd_lonflag = -1
    if data_real[31] == 0x45:
        bd_lonflag = 0
    elif data_real[31] == 0x57:
        bd_lonflag = 1
    d['bd_lonflag'] = bd_lonflag
    d['bd_lon'] = int.from_bytes(data_real[32:36], byteorder='big') * 0.0000001

    bd_latflag = -1
    if data_real[36] == 0x45:
        bd_latflag = 0
    elif data_real[36] == 0x57:
        bd_latflag = 1
    d['bd_latflag'] = bd_latflag
    d['bd_lat'] = int.from_bytes(data_real[37:41], byteorder='big') * 0.0000001
    return d


def parse_03001_type_104(data: bytes):
    d = parse_03001_type_101(data)
    data_real = data[51:]
    d['atmosphere'] = int.from_bytes(data_real[24:27], byteorder='big') * 0.01

    year = data_real[27]
    month = data_real[28]
    day = data_real[29]
    hour = data_real[30]
    minute = data_real[31]
    second = data_real[32]

    d['bd_time'] = date_format(year, month, day, hour, minute, second)
    d['bd_posflag'] = data_real[33]

    bd_lonflag = -1
    if data_real[34] == 0x45:
        bd_lonflag = 0
    elif data_real[34] == 0x57:
        bd_lonflag = 1
    d['bd_lonflag'] = bd_lonflag
    d['bd_lon'] = int.from_bytes(data_real[35:39], byteorder='big') * 0.0000001

    bd_latflag = -1
    if data_real[39] == 0x45:
        bd_latflag = 0
    elif data_real[39] == 0x57:
        bd_latflag = 1
    d['bd_latflag'] = bd_latflag
    d['bd_lat'] = int.from_bytes(data_real[40:44], byteorder='big') * 0.0000001
    return d
