# -*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.db import connections

RAW_DB = 'default'
RAW_SCHEMA = settings.DATABASES.get(RAW_DB, {}).get('NAME', '')


def build_stage_status(result_text: str, is_valid_packet: bool = True) -> str:
    if not is_valid_packet:
        return 'recv_failed'
    if result_text is None:
        return 'parse_failed'
    result_text = str(result_text).strip().lower()
    if result_text.startswith('insert '):
        return 'completed'
    if result_text.startswith('duplicate '):
        return 'db_failed'
    if 'invalid' in result_text:
        return 'parse_failed'
    if result_text in ['success']:
        return 'completed'
    return 'db_failed'


_RECEIVE_LOG_COLUMNS = None


def _get_receive_log_columns():
    global _RECEIVE_LOG_COLUMNS
    if _RECEIVE_LOG_COLUMNS is not None:
        return _RECEIVE_LOG_COLUMNS
    sql = """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 't_receive_log'
    """
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, [RAW_SCHEMA])
        _RECEIVE_LOG_COLUMNS = {row[0] for row in cursor.fetchall()}
    return _RECEIVE_LOG_COLUMNS


def insert_receive_log(
    ip: str,
    request_time: str,
    iridiumid: str,
    sensorflag: str,
    device_id: str,
    sn: int,
    packet_len: int,
    result_status: str,
    message: str,
    raw_hex: str,
    parse_result: str,
):
    columns = _get_receive_log_columns()

    fields = ['ip', 'time', 'device_id', 'iridiumid', 'sensorflag', 'packet_len', 'result', 'ingest_status', 'message', 'raw']
    values = [
        ip,
        _safe_dt(request_time),
        device_id or '',
        iridiumid or '',
        sensorflag or '',
        int(packet_len or 0),
        (result_status or 'failed')[:16],
        '',
        (message or '')[:255],
        raw_hex or '',
    ]

    if 'sn' in columns:
        fields.insert(4, 'sn')
        values.insert(4, int(sn or 0))

    if 'parse_result' in columns:
        raw_idx = fields.index('raw')
        fields.insert(raw_idx + 1, 'parse_result')
        values.insert(raw_idx + 1, (parse_result or '')[:2000])

    field_sql = ', '.join(fields)
    placeholder_sql = ', '.join(['%s'] * len(values))
    sql = f"INSERT INTO t_receive_log ({field_sql}, db_time) VALUES ({placeholder_sql}, NOW())"

    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, values)


def _safe_dt(dt_str: str):
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        return None
