# -*- coding: utf-8 -*-
from ..utils import date_format, bytes_to_iridiumid


def _parse_03004_common_type_401_403_404(data: bytes):
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


def _parse_03004_common_type_402(data: bytes):
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


def _parse_03004_common_type_406(data: bytes):
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


def parse_03004_type_401_part1(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    d['atmosphere'] = int.from_bytes(data_real[24:27], byteorder='big') * 0.01
    d['air_temp'] = int.from_bytes(data_real[27:29], byteorder='big', signed=True) * 0.1
    d['air_humid'] = int.from_bytes(data_real[29:31], byteorder='big') * 0.1
    d['sonar_on'] = int.from_bytes(data_real[31:33], byteorder='big') * 0.001
    d['sonar_under'] = int.from_bytes(data_real[33:36], byteorder='big') * 0.001
    return d


def parse_03004_type_401_part2(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 24 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_1'] = ','.join(temps)
    return d


def parse_03004_type_401_part3(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 24 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_2'] = ','.join(temps)
    return d


def parse_03004_type_402_part1(data: bytes):
    d = _parse_03004_common_type_402(data)
    data_real = data[51:]
    d['sonar_on'] = int.from_bytes(data_real[23:25], byteorder='big') * 0.001
    d['air_temp'] = int.from_bytes(data_real[25:27], byteorder='big', signed=True) * 0.1
    d['air_humid'] = int.from_bytes(data_real[27:29], byteorder='big') * 0.1
    d['sonar_under'] = int.from_bytes(data_real[29:32], byteorder='big') * 0.001
    d['atmosphere'] = int.from_bytes(data_real[32:35], byteorder='big') * 0.01
    return d


def parse_03004_type_402_part2(data: bytes):
    d = _parse_03004_common_type_402(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 23 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_1'] = ','.join(temps)
    return d


def parse_03004_type_402_part3(data: bytes):
    d = _parse_03004_common_type_402(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 23 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_2'] = ','.join(temps)
    return d


def parse_03004_type_403_part1(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    d['atmosphere'] = int.from_bytes(data_real[24:27], byteorder='big') * 0.01
    d['air_temp'] = int.from_bytes(data_real[27:29], byteorder='big', signed=True) * 0.1
    d['air_humid'] = int.from_bytes(data_real[29:31], byteorder='big') * 0.1
    d['sonar_on'] = int.from_bytes(data_real[31:33], byteorder='big') * 0.001
    d['sonar_under'] = int.from_bytes(data_real[33:36], byteorder='big') * 0.001
    d['wind_direct'] = int.from_bytes(data_real[36:38], byteorder='big') * 0.1
    d['wind_speed'] = int.from_bytes(data_real[38:40], byteorder='big') * 0.01
    return d


def parse_03004_type_403_part2(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    temps = []
    for i in range(150):
        start = 24 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC150'] = ','.join(temps)
    return d


def parse_03004_type_404_part1(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    d['atmosphere'] = int.from_bytes(data_real[24:27], byteorder='big') * 0.01
    d['air_temp'] = int.from_bytes(data_real[27:29], byteorder='big', signed=True) * 0.1
    d['air_humid'] = int.from_bytes(data_real[29:31], byteorder='big') * 0.1
    d['sonar_on'] = int.from_bytes(data_real[31:33], byteorder='big') * 0.001
    d['sonar_under'] = int.from_bytes(data_real[33:36], byteorder='big') * 0.001
    return d


def parse_03004_type_404_part2(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]
    temps = []
    for i in range(150):
        start = 24 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC150'] = ','.join(temps)
    return d


def parse_03004_type_405_part1(data: bytes):
    d = _parse_03004_common_type_401_403_404(data)
    data_real = data[51:]

    year = data_real[24]
    month = data_real[25]
    day = data_real[26]
    hour = data_real[27]
    minute = data_real[28]
    second = data_real[29]
    d['bd_time'] = date_format(year, month, day, hour, minute, second)
    d['bd_posflag'] = data_real[30]
    d['bd_lonflag'] = data_real[31]
    d['bd_lon'] = int.from_bytes(data_real[32:36], byteorder='big') * 0.0000001
    d['bd_latflag'] = data_real[36]
    d['bd_lat'] = int.from_bytes(data_real[37:41], byteorder='big') * 0.0000001

    d['atmosphere'] = int.from_bytes(data_real[41:44], byteorder='big') * 0.01
    d['air_temp'] = int.from_bytes(data_real[44:46], byteorder='big', signed=True) * 0.1
    d['air_humid'] = int.from_bytes(data_real[46:48], byteorder='big') * 0.1
    d['sonar_on'] = int.from_bytes(data_real[48:50], byteorder='big') * 0.001
    d['sonar_under'] = int.from_bytes(data_real[50:53], byteorder='big') * 0.001
    return d


def _parse_03004_type_405_part23_common(data: bytes):
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

    board_voltage = int.from_bytes(data_real[9:11], byteorder='big') * 0.001
    board_temp = int.from_bytes(data_real[11:13], byteorder='big', signed=True) * 0.01

    return {
        'iridiumid': iridiumid,
        'sn': sn,
        'time': time,
        'board_voltage': board_voltage,
        'board_temp': board_temp,
    }


def parse_03004_type_405_part2(data: bytes):
    d = _parse_03004_type_405_part23_common(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 13 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_1'] = ','.join(temps)
    return d


def parse_03004_type_405_part3(data: bytes):
    d = _parse_03004_type_405_part23_common(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 13 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_2'] = ','.join(temps)
    return d


def parse_03004_type_406_part1(data: bytes):
    d = _parse_03004_common_type_406(data)
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

    d['atmosphere'] = int.from_bytes(data_real[41:44], byteorder='big') * 0.01
    d['air_temp'] = int.from_bytes(data_real[44:46], byteorder='big', signed=True) * 0.1
    d['air_humid'] = int.from_bytes(data_real[46:48], byteorder='big') * 0.1
    d['sonar_on'] = int.from_bytes(data_real[48:50], byteorder='big') * 0.001
    d['sonar_under'] = int.from_bytes(data_real[50:53], byteorder='big') * 0.001
    return d


def _parse_03004_type_406_part2_common(data: bytes):
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

    board_voltage = int.from_bytes(data_real[9:11], byteorder='big') * 0.001
    board_temp = int.from_bytes(data_real[11:13], byteorder='big', signed=True) * 0.01

    return {
        'iridiumid': iridiumid,
        'sn': sn,
        'time': time,
        'board_voltage': board_voltage,
        'board_temp': board_temp,
    }


def parse_03004_type_406_part2(data: bytes):
    d = _parse_03004_type_406_part2_common(data)
    data_real = data[51:]
    temps = []
    for i in range(100):
        start = 13 + i * 2
        t = int.from_bytes(data_real[start:start + 2], byteorder='big', signed=True) * 0.0625
        temps.append(str(t))
    d['tempC200_1'] = ','.join(temps)
    return d
