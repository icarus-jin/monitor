# -*- coding: utf-8 -*-
from dataclasses import dataclass

from django.db import connections

from utils.log import collector_logger as logger

from .utils import bytes_to_iridiumid
from .parsers.parser_02003 import parse_02003_type_0200301
from .parsers.parser_02006 import parse_02006_type_0200601
from .parsers.parser_02007 import parse_02007_type_0200701
from .parsers.parser_03001 import (
    parse_03001_type_101,
    parse_03001_type_102,
    parse_03001_type_103,
    parse_03001_type_104,
)
from .parsers.parser_03003 import (
    parse_03003_type_301_part1,
    parse_03003_type_301_part2,
)
from .parsers.parser_03004 import (
    parse_03004_type_401_part1,
    parse_03004_type_401_part2,
    parse_03004_type_401_part3,
    parse_03004_type_402_part1,
    parse_03004_type_402_part2,
    parse_03004_type_402_part3,
    parse_03004_type_403_part1,
    parse_03004_type_403_part2,
    parse_03004_type_404_part1,
    parse_03004_type_404_part2,
    parse_03004_type_405_part1,
    parse_03004_type_405_part2,
    parse_03004_type_405_part3,
    parse_03004_type_406_part1,
    parse_03004_type_406_part2,
)
from .parsers.parser_03005 import parse_03005_type_501
from .parsers.parser_03008 import parse_03008_type_0300801


SENSORFLAG_03001_PARSERS = {
    '101': parse_03001_type_101,
    '102': parse_03001_type_102,
    '103': parse_03001_type_103,
    '104': parse_03001_type_104,
}

SENSORFLAG_03004_PARSERS = {
    '401': {
        1: parse_03004_type_401_part1,
        2: parse_03004_type_401_part2,
        3: parse_03004_type_401_part3,
    },
    '402': {
        1: parse_03004_type_402_part1,
        2: parse_03004_type_402_part2,
        3: parse_03004_type_402_part3,
    },
    '403': {
        1: parse_03004_type_403_part1,
        2: parse_03004_type_403_part2,
    },
    '404': {
        1: parse_03004_type_404_part1,
        2: parse_03004_type_404_part2,
    },
    '405': {
        1: parse_03004_type_405_part1,
        2: parse_03004_type_405_part2,
        3: parse_03004_type_405_part3,
    },
    '406': {
        1: parse_03004_type_406_part1,
        2: parse_03004_type_406_part2,
    },
}


@dataclass
class SaveResult:
    result: bool
    reply: str


RAW_DB = 'default'
RAW_SCHEMA = 'jdhydevicedb'


def get_device_by_iridiumid(iridiumid: str):
    sql = "SELECT iridiumid, sensorflag, devid FROM device_list WHERE iridiumid=%s LIMIT 1"
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, [iridiumid])
        row = cursor.fetchone()
    if not row:
        return None
    return {
        'iridiumid': row[0],
        'sensorflag': row[1],
        'devid': row[2],
    }


def data_save(data: bytes) -> SaveResult:
    try:
        iridiumid = bytes_to_iridiumid(data[10:25])
        device = get_device_by_iridiumid(iridiumid)
        if device is None:
            return SaveResult(False, 'invalid iridiumid')

        sensorflag = str(device.get('sensorflag') or '').lower()
        if sensorflag in SENSORFLAG_03001_PARSERS:
            return _save_03001(sensorflag, data, device)
        if sensorflag == '301':
            return _save_03003(data, device)
        if sensorflag in SENSORFLAG_03004_PARSERS:
            return _save_03004(sensorflag, data, device)
        if sensorflag == '501':
            return _save_03005(data, device)
        if sensorflag == '0300801':
            return _save_03008(data, device)
        if sensorflag == '0200601':
            return _save_02006(data, device)
        if sensorflag == '0200701':
            return _save_02007(data, device)
        if sensorflag == '0200301':
            return _save_02003(data, device)

        # TODO: 按设备类型逐步接入解析与入库逻辑
        return SaveResult(False, f'未实现的类型：{sensorflag}')
    except Exception as exc:
        logger.exception('data_save error: %s', exc)
        return SaveResult(False, str(exc))


def parse_payload_by_sensorflag(sensorflag: str, data: bytes) -> dict:
    sensorflag = str(sensorflag or '').lower()
    if sensorflag in SENSORFLAG_03001_PARSERS:
        return SENSORFLAG_03001_PARSERS[sensorflag](data)
    if sensorflag == '301':
        data_xh = data[54]
        if data_xh == 1:
            return parse_03003_type_301_part1(data)
        if data_xh == 2:
            return parse_03003_type_301_part2(data)
        raise ValueError(f'无效的03003分包序号：{data_xh}')
    if sensorflag in SENSORFLAG_03004_PARSERS:
        data_xh = data[53] if sensorflag in {'401', '403', '404', '405', '406'} else data[54]
        parser = SENSORFLAG_03004_PARSERS[sensorflag].get(data_xh)
        if parser is None:
            raise ValueError(f'无效的03004分包序号：{data_xh}')
        return parser(data)
    if sensorflag == '501':
        return parse_03005_type_501(data)
    if sensorflag == '0300801':
        return parse_03008_type_0300801(data)
    if sensorflag == '0200601':
        return parse_02006_type_0200601(data)
    if sensorflag == '0200701':
        return parse_02007_type_0200701(data)
    if sensorflag == '0200301':
        return parse_02003_type_0200301(data)
    raise ValueError(f'未实现的类型：{sensorflag}')


def _insert_if_not_exists(table: str, d: dict) -> bool:
    columns = ','.join(f'`{k}`' for k in d.keys())
    placeholders = ','.join(['%s'] * len(d))
    values = list(d.values())

    sql = (
        f"INSERT INTO {table} ({columns}) "
        f"SELECT {placeholders} FROM dual "
        f"WHERE NOT EXISTS ("
        f"SELECT 1 FROM {table} WHERE iridiumid=%s AND sn=%s"
        f")"
    )
    values.extend([d['iridiumid'], d['sn']])

    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, values)
        return bool(cursor.rowcount)


def _save_03001(sensorflag: str, data: bytes, device: dict) -> SaveResult:
    parser = SENSORFLAG_03001_PARSERS[sensorflag]
    d = parser(data)
    d['devid'] = device['devid']

    table = '`03001idb_icedriftbuoy`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, f'insert 03001_type_{sensorflag} success')
    return SaveResult(True, f'duplicate 03001_type_{sensorflag}')


def _save_03003(data: bytes, device: dict) -> SaveResult:
    data_xh = data[54]
    if data_xh == 1:
        d = parse_03003_type_301_part1(data)
        part = 'part1'
    elif data_xh == 2:
        d = parse_03003_type_301_part2(data)
        part = 'part2'
    else:
        return SaveResult(False, f'无效的03003分包序号：{data_xh}')

    d['devid'] = device['devid']

    table = '`03003uis_unmannedicestation`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, f'insert 03003_type_301_{part} success')
    return SaveResult(True, f'duplicate 03003_type_301_{part}')


def _save_03004(sensorflag: str, data: bytes, device: dict) -> SaveResult:
    data_xh = data[53] if sensorflag in {'401', '403', '404', '405', '406'} else data[54]
    parser = SENSORFLAG_03004_PARSERS[sensorflag].get(data_xh)
    if parser is None:
        return SaveResult(False, f'无效的03004分包序号：{data_xh}')

    d = parser(data)
    d['devid'] = device['devid']

    table = '`03004imb_icemassbalancebuoy`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, f'insert 03004_type_{sensorflag}_part{data_xh} success')
    return SaveResult(True, f'duplicate 03004_type_{sensorflag}_part{data_xh}')


def _save_03005(data: bytes, device: dict) -> SaveResult:
    d = parse_03005_type_501(data)
    d['devid'] = device['devid']

    table = '`03005mp_meltpond`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, 'insert 03005_type_501 success')
    return SaveResult(True, 'duplicate 03005_type_501')


def _save_03008(data: bytes, device: dict) -> SaveResult:
    d = parse_03008_type_0300801(data)
    d['devid'] = device['devid']

    table = '`03008isb_icestressbuoy`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, 'insert 03008_type_0300801 success')
    return SaveResult(True, 'duplicate 03008_type_0300801')


def _save_02006(data: bytes, device: dict) -> SaveResult:
    d = parse_02006_type_0200601(data)
    d['devid'] = device['devid']

    table = '`02006cr_cornerreflector`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, 'insert 02006_type_0200601 success')
    return SaveResult(True, 'duplicate 02006_type_0200601')


def _save_02007(data: bytes, device: dict) -> SaveResult:
    d = parse_02007_type_0200701(data)
    d['devid'] = device['devid']

    table = '`02007stb_southtempchainbuoy`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, 'insert 02007_type_0200701 success')
    return SaveResult(True, 'duplicate 02007_type_0200701')


def _save_02003(data: bytes, device: dict) -> SaveResult:
    d = parse_02003_type_0200301(data)
    d['devid'] = device['devid']

    table = '`02003spom_spacephysicsobservationmodule`'
    inserted = _insert_if_not_exists(table, d)
    if inserted:
        return SaveResult(True, 'insert 02003_type_0200301 success')
    return SaveResult(True, 'duplicate 02003_type_0200301')
