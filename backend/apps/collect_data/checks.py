# -*- coding: utf-8 -*-

def bytes_to_hex(data: bytes) -> str:
    return " ".join(f"{b:02x}" for b in data)


def check_data(data: bytes) -> bool:
    length = len(data)
    if length < 3:
        return False
    if data[0] != 0x01:
        return False
    rlen = int.from_bytes(data[1:3], byteorder="big", signed=False)
    if length - 3 != rlen:
        return False
    if length <= 51:
        return False
    if data[51] != 0x5B or data[length - 1] != 0x5D:
        return False
    return True
