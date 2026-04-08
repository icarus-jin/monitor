# -*- coding: utf-8 -*-

def date_format(year, month, day, hour, minute, second):
    year = f"20{year}" if year > 9 else f"200{year}"
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def bytes_to_iridiumid(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")
