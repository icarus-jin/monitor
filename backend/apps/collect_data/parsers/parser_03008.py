# -*- coding: utf-8 -*-
import struct

from ..utils import date_format, bytes_to_iridiumid


def parse_03008_type_0300801(data: bytes):
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

    stress1_data = data_real[24:108]
    stress_realdata = bytearray()
    for i in range(6):
        start_index = i * 14
        stress_realdata.extend(stress1_data[start_index + 6:start_index + 14])

    stress_values = []
    for i in range(0, len(stress_realdata), 4):
        float_value = struct.unpack('<f', stress_realdata[i:i + 4])[0]
        stress_values.append(f"{float_value:.4f}")

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
        'stressdata': ','.join(stress_values),
    }
