# -*- coding: utf-8 -*-
"""
设备视图（只读展示模式）
- 用户权限：jdhydevicedb.t_user
- 设备/业务数据：jdhydevicedb 原始库
"""
from datetime import datetime
import time
from pathlib import Path
from threading import Lock, Event

from django.db import connections
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse

import random
import requests

from apps.user.models import User
from utils import success, error, logger, token_store

RAW_DB = 'default'
RAW_SCHEMA = 'jdhydevicedb'

PREFIX_TABLE_MAP = {
    '01001': '01001gnssstation',
    '02001': '02001ugms_unattendedglaciermonitoringsystem',
    '02002': '02002ms_meteorologicalstation',
    '02003': '02003spom_spacephysicsobservationmodule',
    '02004': '02004sib_seaicebuoy',
    '02005': '02005pmc_penguinmonitoringcamera',
    '02006': '02006cr_cornerreflector',
    '02007': '02007stb_southtempchainbuoy',
    '03001': '03001idb_icedriftbuoy',
    '03002': '03002tcb_tempchainbuoy',
    '03003': '03003uis_unmannedicestation',
    '03004': '03004imb_icemassbalancebuoy',
    '03005': '03005mp_meltpond',
    '03006': '03006ib_imagebuoy',
    '03007': '03007ab_adcpbuoy',
    '03008': '03008isb_icestressbuoy'
}

_table_columns_cache = {}

MAP_POINTS_CACHE_TTL_SECONDS = 20
_map_points_cache = {}
_map_points_cache_lock = Lock()


def _get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        token = request.META.get('HTTP_AUTHORIZATION') or request.GET.get('token')
        info = token_store.get(token)
        if info:
            user_id = info.get('user_id')
    if not user_id:
        return None
    return User.objects.using(RAW_DB).filter(id=user_id, is_delete=0).first()


def _normalize_lat_lon(lat, lon, latflag, lonflag):
    try:
        if lat is not None:
            lat = float(lat)
            lat = -abs(lat) if int(latflag or 0) == 1 else abs(lat)
        if lon is not None:
            lon = float(lon)
            lon = -abs(lon) if int(lonflag or 0) == 1 else abs(lon)
            while lon > 180:
                lon -= 360
            while lon < -180:
                lon += 360
        return lat, lon
    except Exception:
        return None, None


def _device_type_from_prefix(prefix5):
    if str(prefix5 or '').startswith('01'):
        return 'station'
    return 'buoy'


def _device_type_from_device_id(device_id):
    return _device_type_from_prefix(_prefix_from_devid(device_id))


def _to_naive(dt):
    if not dt:
        return None
    if timezone.is_aware(dt):
        return timezone.localtime(dt).replace(tzinfo=None)
    return dt


def _fmt_dt(dt):
    dt = _to_naive(dt)
    if not dt:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _is_online_time(dt):
    dt = _to_naive(dt)
    if not dt:
        return False
    now_naive = timezone.localtime(timezone.now()).replace(tzinfo=None)
    return dt >= now_naive - timezone.timedelta(hours=24)


def _dict_fetch_all(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _dict_fetch_one(cursor):
    row = cursor.fetchone()
    if not row:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def _get_comment_map(table_name):
    sql = """
    SELECT column_name, column_comment
    FROM information_schema.columns
    WHERE table_schema=%s AND table_name=%s
    ORDER BY ordinal_position
    """
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, [RAW_SCHEMA, table_name])
        rows = cursor.fetchall()
    return {r[0]: (r[1] or '').strip() for r in rows}


FIELD_LABEL_MAP = {
    'id': '序号',
    'name': '设备名称',
    'devid': '设备序列号',
    'iridiumid': '铱星号',
    'sensorflag': '传感器标志位',
    'latflag': '纬度标志位',
    'lat': '纬度',
    'lonflag': '经度标志位',
    'lon': '经度',
    'workstate': '工作状态',
    'display': '同步标志位',
    'ownership': '归属单位',
    'sn': '铱星数据编号',
    'db_time': '入库时间',
    'uploaded': '同步标志位',
    'time': '本地时间',
    'BDid': '北斗号',
    'Boardtemp': '控制器温度',
    'Btyvoltage': '电池电压',
    'Btycurrent': '电池电流',
    'Loadpower': '负载功率',
    'Solarvoltage': '光伏板电压',
    'Solarcurrent': '光伏板电流',
    'Solarpower': '光伏板功率',
    'Dayconsump': '日耗电量',
    'Daygenerat': '日发电量',
    'Lightness': '光照强度',
    'VWC_voltage': '土壤体积含水量-电压',
    'VWC_temp': '土壤体积含水量-温度',
    'EC_voltage': '土壤电导率-电压',
    'EC_temp': '土壤电导率-温度',
    'T_voltage': '土壤温度-电压',
    'T_temp': '土壤温度-温度',
    'SoilDATA': '土壤数据',
    'board_voltage': '控制器电压',
    'board_temp': '控制器温度',
    'acpdu_status': '交流PDU状态',
    'acpdu_voltage': '交流PDU电压',
    'acpdu_current': '交流PDU电流',
    'solar_radiation': '光伏板辐照度',
    'solar_batt_voltage': '光伏系统电池电压',
    'solar_voltage': '光伏板电压',
    'solar_charge_current': '光伏板充电电流',
    'batt_capacity': '电池容量',
    'solar_generation': '光伏发电量',
    'ctrl_temp': '光伏系统控制器温度',
    'voltage': '电压',
    'current': '电流',
    'power': '功率',
    'dcpdu_status': '直流PDU状态',
    'dcpdu_voltage': '直流PDU电压',
    'dcpdu_current': '直流PDU电流',
    'cabin_temp': '能源舱温度',
    'cabin_humid': '能源舱适度',
    'wind_batt_voltage': '风机系统电池电压',
    'wind_charge_current': '风机系统充电电流',
    'wind_voltage': '风机系统电压',
    'wind_current': '风机系统电流',
    'wind_instant_power': '风机系统实时功率',
    'wind_total_generation': '风机系统总发电量',
    'wind_rotatespeed': '风机系统风速',
    'wind_status': '风机系统状态',
    'atmosphere': '大气压力',
    'air_temp': '空气温度',
    'wind_direct': '风向',
    'wind_speed': '风速',
    'tempC40': '半导体温度链_40P',
    'tempC150': '半导体温度链_150P',
    'tempC200_1': '半导体温度链_200P-01',
    'tempC200_2': '半导体温度链_200P-02',
    'tempC_pt': '铂电阻温度链',
    'tempC_bio': '半导体温度链',
    'air_humid': '空气湿度',
    'sonar_on': '超声波雪深声呐',
    'sonar_under': '冰下仰视声呐',
    'ST_temp': '皮温传感器',
    'CTD_c2': 'CTD_电导率',
    'CTD_t2': 'CTD_温度',
    'CTD_v2': 'CTD_声速',
    'CTD_s2': 'CTD_盐度',
    'CTD_d2': 'CTD_比电导率',
    'bd_time': '北斗时间',
    'bd_posflag': '北斗定位标志位',
    'bd_latflag': '北斗纬度标志位',
    'bd_lat': '北斗纬度',
    'bd_lonflag': '北斗经度标志位',
    'bd_lon': '北斗经度',
    'ADCP_data': 'ADCP数据',
    'stressdata': '海冰应力数据'
}


def _field_label(field, comment_map):
    return FIELD_LABEL_MAP.get(field, field)


def _prefix_from_devid(device_id):
    return (str(device_id or '').strip())[:5]


def _table_by_device_id(device_id):
    return PREFIX_TABLE_MAP.get(_prefix_from_devid(device_id))


def _table_columns(table_name):
    if table_name in _table_columns_cache:
        return _table_columns_cache[table_name]

    sql = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema=%s AND table_name=%s
    ORDER BY ordinal_position
    """
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, [RAW_SCHEMA, table_name])
        rows = cursor.fetchall()
    cols = [r[0] for r in rows]
    _table_columns_cache[table_name] = cols
    return cols


def _device_ids_grouped_by_table(device_ids):
    grouped = {}
    for did in device_ids:
        table_name = _table_by_device_id(did)
        if not table_name:
            continue
        grouped.setdefault(table_name, []).append(did)
    return grouped


def _get_latest_time_map(device_ids):
    if not device_ids:
        return {}

    latest_map = {}
    grouped = _device_ids_grouped_by_table(device_ids)

    with connections[RAW_DB].cursor() as cursor:
        for table_name, dids in grouped.items():
            cols = set(_table_columns(table_name))
            if 'devid' not in cols or 'time' not in cols:
                continue

            placeholders = ','.join(['%s'] * len(dids))
            sql = f"""
            SELECT devid, MAX(`time`) AS latest_time
            FROM `{table_name}`
            WHERE devid IN ({placeholders}) AND `time` IS NOT NULL
            GROUP BY devid
            """
            try:
                cursor.execute(sql, dids)
                for devid, latest_time in cursor.fetchall():
                    if devid:
                        latest_map[devid] = latest_time
            except Exception:
                continue

    return latest_map


def _get_latest_position_map(device_ids):
    """按设备返回最新有效经纬度（按devid前5位路由到对应业务表）。"""
    if not device_ids:
        return {}

    latest_pos = {}
    grouped = _device_ids_grouped_by_table(device_ids)

    with connections[RAW_DB].cursor() as cursor:
        for table_name, dids in grouped.items():
            cols = set(_table_columns(table_name))
            required = {'devid', 'time', 'lat', 'lon'}
            if not required.issubset(cols):
                continue

            latflag_expr = 'latflag' if 'latflag' in cols else 'NULL'
            lonflag_expr = 'lonflag' if 'lonflag' in cols else 'NULL'
            placeholders = ','.join(['%s'] * len(dids))

            sql = f"""
            SELECT t.devid, t.`time` AS packet_time, {latflag_expr} AS latflag, t.lat, {lonflag_expr} AS lonflag, t.lon
            FROM `{table_name}` t
            INNER JOIN (
              SELECT devid, MAX(`time`) AS latest_time
              FROM `{table_name}`
              WHERE devid IN ({placeholders}) AND `time` IS NOT NULL
              GROUP BY devid
            ) m ON t.devid = m.devid AND t.`time` = m.latest_time
            """
            try:
                cursor.execute(sql, dids)
                rows = cursor.fetchall()
            except Exception:
                continue

            for devid, packet_time, latflag, lat, lonflag, lon in rows:
                nlat, nlon = _normalize_lat_lon(lat, lon, latflag, lonflag)
                if nlat is None or nlon is None:
                    continue
                latest_pos[devid] = {
                    'latitude': nlat,
                    'longitude': nlon,
                    'packet_time': packet_time
                }

    return latest_pos


def _get_latest_row_by_device(table_name, device_id):
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM `{table_name}` WHERE devid=%s AND `time` IS NOT NULL ORDER BY `time` DESC LIMIT 1",
            [device_id]
        )
        return _dict_fetch_one(cursor)


def _build_trend_fields(table_name):
    cols = _table_columns(table_name)
    excluded = {'id', 'devid'}
    fields = [c for c in cols if c not in excluded]
    if 'time' in fields:
        fields.remove('time')
        fields.insert(0, 'time')
    return fields


def _safe_float(v):
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _build_latest_payload(latest_row):
    lat = _safe_float(latest_row.get('lat'))
    lon = _safe_float(latest_row.get('lon'))
    if lat is not None or lon is not None:
        nlat, nlon = _normalize_lat_lon(lat, lon, latest_row.get('latflag'), latest_row.get('lonflag'))
    else:
        nlat, nlon = None, None

    payload = {
        'packet_time': _fmt_dt(latest_row.get('time')),
        'latitude': nlat,
        'longitude': nlon
    }

    for k, v in latest_row.items():
        if k == 'time':
            continue
        payload[k] = v
    return payload


def _get_latest_row_for_device(device_id):
    table_name = _table_by_device_id(device_id)
    if not table_name:
        return None, None
    row = _get_latest_row_by_device(table_name, device_id)
    if not row:
        return table_name, None
    return table_name, row


def _empty_trend_payload(device_id, source_table, range_type, start_dt, end_dt, page, page_size):
    return {
        'device_id': device_id,
        'source_table': source_table or '',
        'range_type': range_type,
        'start_date': start_dt.strftime('%Y-%m-%d'),
        'end_date': end_dt.strftime('%Y-%m-%d'),
        'total': 0,
        'page': page,
        'page_size': page_size,
        'columns': [],
        'points': []
    }


def _default_year_range():
    now = timezone.localtime(timezone.now())
    start = datetime(now.year, 1, 1, 0, 0, 0)
    end = datetime(now.year, 12, 31, 23, 59, 59)
    return start, end


def _parse_date_range(start_date, end_date):
    if not start_date or not end_date:
        return _default_year_range()
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        if start > end:
            start, end = end, start
        return start, end
    except Exception:
        return _default_year_range()


def _map_points_cache_key(user):
    if user.type == 1:
        return 'admin:all'
    device_ids = sorted([str(x) for x in (user.device_list or [])])
    return f"user:{user.id}:" + ','.join(device_ids)


def _map_points_cache_get(cache_key):
    now = time.time()
    with _map_points_cache_lock:
        item = _map_points_cache.get(cache_key)
        if not item:
            return None
        if now - item['ts'] > MAP_POINTS_CACHE_TTL_SECONDS:
            _map_points_cache.pop(cache_key, None)
            return None
        return item['data']


def _map_points_cache_set(cache_key, data):
    with _map_points_cache_lock:
        _map_points_cache[cache_key] = {
            'ts': time.time(),
            'data': data
        }


@method_decorator(csrf_exempt, name='dispatch')
class DeviceListView(View):
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            keyword = (request.GET.get('keyword') or '').strip()
            ownership = (request.GET.get('ownership') or '').strip()
            status_filter = request.GET.get('status')
            use_latest_position = request.GET.get('use_latest_position') in ['1', 'true', 'True']

            sql = """
            SELECT id, name, devid, iridiumid, sensorflag, latflag, lat, lonflag, lon, workstate, display, ownership
            FROM `device_list`
            WHERE 1=1
            """
            params = []

            if keyword:
                sql += " AND (devid LIKE %s OR name LIKE %s OR ownership LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

            if user.type != 1:
                device_ids = user.device_list or []
                if not device_ids:
                    return success(data={'device_list': [], 'total': 0})
                placeholders = ','.join(['%s'] * len(device_ids))
                sql += f" AND devid IN ({placeholders})"
                params.extend(device_ids)

            sql += " ORDER BY devid ASC"

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            raw_list = []
            for row in rows:
                raw_id, name, devid, iridiumid, sensorflag, latflag, lat, lonflag, lon, workstate, display_flag, own = row
                nlat, nlon = _normalize_lat_lon(lat, lon, latflag, lonflag)
                raw_list.append({
                    'id': int(raw_id) if raw_id is not None else 0,
                    'name': name or '',
                    'device_name': name or devid,
                    'devid': devid,
                    'device_id': devid,
                    'iridiumid': iridiumid or '',
                    'iridium_id': iridiumid or '',
                    'sensorflag': sensorflag or '',
                    'latflag': int(latflag) if latflag is not None else None,
                    'lat': nlat,
                    'latitude': nlat,
                    'lonflag': int(lonflag) if lonflag is not None else None,
                    'lon': nlon,
                    'longitude': nlon,
                    'workstate': int(workstate) if workstate is not None else None,
                    'display': int(display_flag) if display_flag is not None else None,
                    'ownership': own or '',
                    'prefix5': _prefix_from_devid(devid),
                    'source_table': _table_by_device_id(devid) or '',
                    'device_type': _device_type_from_device_id(devid)
                })

            if ownership:
                raw_list = [x for x in raw_list if ownership in x['ownership']]

            device_ids = [x['device_id'] for x in raw_list]
            latest_map = _get_latest_time_map(device_ids)
            latest_pos_map = _get_latest_position_map(device_ids) if use_latest_position else {}
            for x in raw_list:
                t = latest_map.get(x['device_id'])
                x['status'] = 1 if _is_online_time(t) else 0
                x['status_name'] = '在线' if x['status'] == 1 else '离线'
                x['last_report_time'] = _fmt_dt(t)
                if use_latest_position:
                    pos = latest_pos_map.get(x['device_id'])
                    if pos:
                        x['latitude'] = pos.get('latitude')
                        x['longitude'] = pos.get('longitude')
                        x['latest_packet_time'] = _fmt_dt(pos.get('packet_time'))

            if status_filter in ['0', '1']:
                raw_list = [x for x in raw_list if x['status'] == int(status_filter)]

            total = len(raw_list)
            paginator = Paginator(raw_list, page_size)
            page_obj = paginator.get_page(page)
            return success(data={'device_list': list(page_obj), 'total': total})
        except Exception as e:
            logger.exception('设备列表异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceSimpleListView(View):
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            keyword = (request.GET.get('keyword') or '').strip()
            sql = "SELECT id, devid, name, ownership FROM `device_list` WHERE 1=1"
            params = []
            if keyword:
                sql += " AND (devid LIKE %s OR name LIKE %s OR ownership LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            if user.type != 1:
                device_ids = user.device_list or []
                if not device_ids:
                    return success(data={'device_list': []})
                placeholders = ','.join(['%s'] * len(device_ids))
                sql += f" AND devid IN ({placeholders})"
                params.extend(device_ids)
            sql += " ORDER BY devid ASC"

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            device_list = [
                {
                    'id': int(r[0]) if r[0] is not None else i + 1,
                    'device_id': r[1],
                    'device_name': r[2] or r[1],
                    'ownership': r[3] or ''
                }
                for i, r in enumerate(rows)
            ]
            return success(data={'device_list': device_list})
        except Exception as e:
            logger.exception('设备简要列表异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceMapPointsView(View):
    """首页地图设备点位（一次返回，使用最新有效经纬度）。"""
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            cache_key = _map_points_cache_key(user)
            cached = _map_points_cache_get(cache_key)
            if cached is not None:
                return success(data=cached)

            sql = "SELECT id, devid, name, ownership FROM `device_list` WHERE 1=1"
            params = []
            if user.type != 1:
                device_ids = user.device_list or []
                if not device_ids:
                    payload = {'device_list': [], 'total': 0}
                    _map_points_cache_set(cache_key, payload)
                    return success(data=payload)
                placeholders = ','.join(['%s'] * len(device_ids))
                sql += f" AND devid IN ({placeholders})"
                params.extend(device_ids)
            sql += " ORDER BY devid ASC"

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            # device_list 可能存在重复 devid，按 device_id 去重（保留最新一条）
            base_device_map = {}
            for row in rows:
                raw_id, devid, name, own = row
                if not devid:
                    continue
                base_device_map[devid] = {
                    'id': int(raw_id) if raw_id is not None else 0,
                    'device_id': devid,
                    'device_name': name or devid,
                    'prefix5': _prefix_from_devid(devid),
                    'source_table': _table_by_device_id(devid) or '',
                    'ownership': own or '',
                    'device_type': _device_type_from_device_id(devid)
                }
            base_devices = list(base_device_map.values())

            device_ids = [x['device_id'] for x in base_devices]
            latest_map = _get_latest_time_map(device_ids)
            latest_pos_map = _get_latest_position_map(device_ids)

            point_list = []
            for item in base_devices:
                pos = latest_pos_map.get(item['device_id'])
                if not pos:
                    continue
                t = latest_map.get(item['device_id'])
                is_online = _is_online_time(t)
                point_list.append({
                    **item,
                    'latitude': pos.get('latitude'),
                    'longitude': pos.get('longitude'),
                    'latest_packet_time': _fmt_dt(pos.get('packet_time')),
                    'status': 1 if is_online else 0,
                    'status_name': '在线' if is_online else '离线',
                    'last_report_time': _fmt_dt(t)
                })

            payload = {'device_list': point_list, 'total': len(point_list)}
            _map_points_cache_set(cache_key, payload)
            return success(data=payload)
        except Exception as e:
            logger.exception('首页地图点位异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceDetailView(View):
    def post(self, request):
        return error('当前阶段设备信息从原始库读取，暂不支持新增', code=400)

    def put(self, request):
        return error('当前阶段设备信息从原始库读取，暂不支持编辑', code=400)

    def delete(self, request):
        return error('当前阶段设备信息从原始库读取，暂不支持删除', code=400)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceBatchDeleteView(View):
    def post(self, request):
        return error('当前阶段设备信息从原始库读取，暂不支持批量删除', code=400)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceDataIngestView(View):
    def post(self, request):
        return error('当前阶段业务数据全部从原始库读取，暂不支持写入', code=400)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceDataLatestView(View):
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            device_id = (request.GET.get('device_id') or '').strip()
            if not device_id:
                return error('device_id不能为空', code=400)
            if user.type != 1 and device_id not in (user.device_list or []):
                return error('设备不存在或无权限', code=404)

            source_table, latest_row = _get_latest_row_for_device(device_id)
            if not source_table:
                return success(data={'device_id': device_id, 'source_table': '', 'latest': None, 'field_list': []})
            if not latest_row:
                return success(data={'device_id': device_id, 'source_table': source_table, 'latest': None, 'field_list': []})

            comment_map = _get_comment_map(source_table)
            field_list = []
            for k, v in latest_row.items():
                if k in ['id', 'devid']:
                    continue
                if k == 'time':
                    v = _fmt_dt(v)
                field_list.append({'field': k, 'label': _field_label(k, comment_map), 'value': v})

            return success(data={
                'device_id': device_id,
                'source_table': source_table,
                'latest': _build_latest_payload(latest_row),
                'field_list': field_list
            })
        except Exception as e:
            logger.exception('获取设备最新数据异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceTrendView(View):
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            device_id = (request.GET.get('device_id') or '').strip()
            range_type = (request.GET.get('range_type') or 'year').strip()
            start_date = (request.GET.get('start_date') or '').strip()
            end_date = (request.GET.get('end_date') or '').strip()
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 100))

            if not device_id:
                return error('device_id不能为空', code=400)
            if user.type != 1 and device_id not in (user.device_list or []):
                return error('设备不存在或无权限', code=404)

            if range_type == '24h':
                end_dt = _to_naive(timezone.now())
                start_dt = end_dt - timezone.timedelta(hours=24)
            elif range_type == '7d':
                end_dt = _to_naive(timezone.now())
                start_dt = end_dt - timezone.timedelta(days=7)
            else:
                start_dt, end_dt = _parse_date_range(start_date, end_date)

            offset = (page - 1) * page_size

            source_table = _table_by_device_id(device_id)
            if not source_table:
                return success(data=_empty_trend_payload(device_id, '', range_type, start_dt, end_dt, page, page_size))

            cols = set(_table_columns(source_table))
            if 'devid' not in cols or 'time' not in cols:
                return success(data=_empty_trend_payload(device_id, source_table, range_type, start_dt, end_dt, page, page_size))

            fields = _build_trend_fields(source_table)
            comment_map = _get_comment_map(source_table)
            columns = [{'field': f, 'label': _field_label(f, comment_map)} for f in fields if f != 'time']

            count_sql = f"SELECT COUNT(*) FROM `{source_table}` WHERE devid=%s AND `time` BETWEEN %s AND %s"
            data_sql = f"SELECT * FROM `{source_table}` WHERE devid=%s AND `time` BETWEEN %s AND %s ORDER BY `time` DESC LIMIT %s OFFSET %s"

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(count_sql, [device_id, start_dt, end_dt])
                total_count = cursor.fetchone()[0]

                cursor.execute(data_sql, [device_id, start_dt, end_dt, page_size, offset])
                rows = _dict_fetch_all(cursor)

            points = []
            for r in rows:
                item = {
                    'time': _fmt_dt(r.get('time')),
                    'source_table': source_table
                }
                for f in fields:
                    item[f] = r.get(f)
                points.append(item)

            return success(data={
                'device_id': device_id,
                'source_table': source_table,
                'range_type': range_type,
                'start_date': start_dt.strftime('%Y-%m-%d'),
                'end_date': end_dt.strftime('%Y-%m-%d'),
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'columns': columns,
                'points': points
            })
        except Exception as e:
            logger.exception('获取设备趋势数据异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceTrackView(View):
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            device_id = (request.GET.get('device_id') or '').strip()
            limit = int(request.GET.get('limit', 600))
            start_date = (request.GET.get('start_date') or '').strip()
            end_date = (request.GET.get('end_date') or '').strip()
            if not device_id:
                return error('device_id不能为空', code=400)
            if user.type != 1 and device_id not in (user.device_list or []):
                return error('设备不存在或无权限', code=404)

            source_table = _table_by_device_id(device_id)
            if not source_table:
                return success(data={'device_id': device_id, 'source_table': '', 'point_count': 0, 'points': []})

            cols = set(_table_columns(source_table))
            required = {'devid', 'time', 'lat', 'lon'}
            if not required.issubset(cols):
                return success(data={'device_id': device_id, 'source_table': source_table, 'point_count': 0, 'points': []})

            start_dt, end_dt = _parse_date_range(start_date, end_date)

            latflag_expr = 'latflag' if 'latflag' in cols else 'NULL'
            lonflag_expr = 'lonflag' if 'lonflag' in cols else 'NULL'
            sql = f"""
            SELECT `time` AS packet_time, {latflag_expr} AS latflag, lat, {lonflag_expr} AS lonflag, lon
            FROM `{source_table}`
            WHERE devid=%s
              AND lat IS NOT NULL
              AND lon IS NOT NULL
              AND `time` IS NOT NULL
              AND `time` BETWEEN %s AND %s
            ORDER BY `time` DESC
            LIMIT %s
            """
            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(sql, [device_id, start_dt, end_dt, limit])
                rows = cursor.fetchall()

            points = []
            for r in reversed(rows):
                lat, lon = _normalize_lat_lon(r[2], r[4], r[1], r[3])
                if lat is None or lon is None:
                    continue
                points.append({'time': _fmt_dt(r[0]), 'lat': lat, 'lng': lon})

            return success(data={
                'device_id': device_id,
                'source_table': source_table,
                'point_count': len(points),
                'start_date': start_dt.strftime('%Y-%m-%d'),
                'end_date': end_dt.strftime('%Y-%m-%d'),
                'points': points
            })
        except Exception as e:
            logger.exception('获取设备轨迹异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceOverviewView(View):
    def get(self, request):
        try:
            user = _get_current_user(request)
            if not user:
                return error('登录状态已失效，请重新登录', code=10016)

            sql = "SELECT devid, ownership FROM `device_list`"
            params = []
            if user.type != 1:
                device_ids = user.device_list or []
                if not device_ids:
                    return success(data={'total_devices': 0, 'online_devices': 0, 'offline_devices': 0, 'total_users': 1, 'buoy_count': 0, 'station_count': 0, 'area_stats': {'南极': 0, '北极': 0, '亚太': 0}, 'data_quality': {'total_data_packets': 0, 'valid_position_packets': 0, 'position_valid_rate': 0, 'latest_packet_time': ''}})
                placeholders = ','.join(['%s'] * len(device_ids))
                sql += f" WHERE devid IN ({placeholders})"
                params.extend(device_ids)

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(sql, params)
                devices = cursor.fetchall()

            total_devices = len(devices)
            buoy_count, station_count = 0, 0
            areas = {'南极': 0, '北极': 0, '亚太': 0}
            devids = []
            for d in devices:
                devids.append(d[0])
                dt = _device_type_from_device_id(d[0])
                own = (d[1] or '')
                if dt == 'station':
                    station_count += 1
                else:
                    buoy_count += 1
                if '南极' in own:
                    areas['南极'] += 1
                elif '北极' in own:
                    areas['北极'] += 1
                else:
                    areas['亚太'] += 1

            latest_map = _get_latest_time_map(devids)
            online_devices = sum(1 for v in latest_map.values() if _is_online_time(v))
            total_users = User.objects.using(RAW_DB).filter(is_delete=0).count() if user.type == 1 else 1

            total_packets = 0
            valid_packets = 0
            latest_packet = None

            if devids:
                grouped = _device_ids_grouped_by_table(devids)
                with connections[RAW_DB].cursor() as cursor:
                    for table_name, dids in grouped.items():
                        cols = set(_table_columns(table_name))
                        if 'devid' not in cols or 'time' not in cols:
                            continue

                        placeholders = ','.join(['%s'] * len(dids))
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE devid IN ({placeholders})", dids)
                            total_packets += cursor.fetchone()[0]
                        except Exception:
                            continue

                        if 'lat' in cols and 'lon' in cols:
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}` WHERE devid IN ({placeholders}) AND lat IS NOT NULL AND lon IS NOT NULL", dids)
                                valid_packets += cursor.fetchone()[0]
                            except Exception:
                                pass

                        try:
                            cursor.execute(f"SELECT MAX(`time`) FROM `{table_name}` WHERE devid IN ({placeholders})", dids)
                            t = cursor.fetchone()[0]
                            if t and (not latest_packet or _to_naive(t) >= _to_naive(latest_packet)):
                                latest_packet = t
                        except Exception:
                            pass

            return success(data={
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': total_devices - online_devices,
                'total_users': total_users,
                'buoy_count': buoy_count,
                'station_count': station_count,
                'area_stats': areas,
                'data_quality': {
                    'total_data_packets': total_packets,
                    'valid_position_packets': valid_packets,
                    'position_valid_rate': round((valid_packets / total_packets) * 100, 2) if total_packets else 0,
                    'latest_packet_time': _fmt_dt(latest_packet)
                }
            })
        except Exception as e:
            logger.exception('概览数据异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class MapTileProxyView(View):
    _CACHE_TTL_SECONDS = 1800
    _MEMORY_CACHE_MAX_ITEMS = 4000
    _DISK_CACHE_MAX_BYTES = 20 * 1024 * 1024 * 1024  # 20GB
    _DISK_USAGE_REFRESH_SECONDS = 60
    _cache = {}
    _inflight = {}
    _cache_lock = Lock()
    _disk_cache_root = Path(__file__).resolve().parents[2] / 'cache' / 'map_tiles'
    _disk_usage_bytes = 0
    _last_usage_check_ts = 0

    @classmethod
    def _cache_key(cls, x, y, z, style, lang):
        return f'{style}:{lang}:{z}:{x}:{y}'

    @classmethod
    def _disk_tile_path(cls, x, y, z, style, lang):
        tile_dir = cls._disk_cache_root / str(style) / str(lang) / str(z) / str(x)
        return tile_dir / f'{y}.tile'

    @classmethod
    def _disk_meta_path(cls, x, y, z, style, lang):
        tile_dir = cls._disk_cache_root / str(style) / str(lang) / str(z) / str(x)
        return tile_dir / f'{y}.meta'

    @classmethod
    def _get_disk_usage_bytes(cls, force=False):
        now = time.time()
        with cls._cache_lock:
            if (not force) and cls._disk_usage_bytes > 0 and (now - cls._last_usage_check_ts) < cls._DISK_USAGE_REFRESH_SECONDS:
                return cls._disk_usage_bytes

        total = 0
        root = cls._disk_cache_root
        if root.exists():
            try:
                for path in root.rglob('*.tile'):
                    if path.is_file():
                        total += path.stat().st_size
            except Exception as e:
                logger.warning('统计瓦片磁盘占用失败: %s', e)

        with cls._cache_lock:
            cls._disk_usage_bytes = total
            cls._last_usage_check_ts = now
        return total

    @classmethod
    def _can_write_disk_cache(cls, incoming_size, current_tile_size=0):
        used = cls._get_disk_usage_bytes(force=False)
        projected = used - max(current_tile_size, 0) + max(incoming_size, 0)
        return projected <= cls._DISK_CACHE_MAX_BYTES

    @classmethod
    def _get_from_cache(cls, key):
        now = time.time()
        with cls._cache_lock:
            item = cls._cache.get(key)
            if not item:
                return None
            if now - item['ts'] > cls._CACHE_TTL_SECONDS:
                cls._cache.pop(key, None)
                return None
            return item

    @classmethod
    def _set_cache(cls, key, content, content_type):
        with cls._cache_lock:
            cls._cache[key] = {
                'ts': time.time(),
                'content': content,
                'content_type': content_type
            }
            if len(cls._cache) > cls._MEMORY_CACHE_MAX_ITEMS:
                drop_count = max(1, len(cls._cache) - cls._MEMORY_CACHE_MAX_ITEMS)
                oldest_keys = sorted(cls._cache.keys(), key=lambda k: cls._cache[k]['ts'])[:drop_count]
                for k in oldest_keys:
                    cls._cache.pop(k, None)

    @classmethod
    def _get_from_disk_cache(cls, x, y, z, style, lang):
        tile_path = cls._disk_tile_path(x, y, z, style, lang)
        meta_path = cls._disk_meta_path(x, y, z, style, lang)
        if not tile_path.exists():
            return None

        try:
            content = tile_path.read_bytes()
            if not content:
                return None

            content_type = 'image/png'
            if meta_path.exists():
                try:
                    meta_content = meta_path.read_text(encoding='utf-8').strip()
                    if meta_content:
                        content_type = meta_content
                except Exception:
                    pass

            return {
                'content': content,
                'content_type': content_type
            }
        except Exception as e:
            logger.warning('读取瓦片磁盘缓存失败 %s: %s', tile_path, e)
            return None

    @classmethod
    def _set_disk_cache(cls, x, y, z, style, lang, content, content_type):
        tile_path = cls._disk_tile_path(x, y, z, style, lang)
        meta_path = cls._disk_meta_path(x, y, z, style, lang)
        try:
            current_tile_size = tile_path.stat().st_size if tile_path.exists() else 0
            incoming_size = len(content or b'')
            if incoming_size <= 0:
                return False
            if not cls._can_write_disk_cache(incoming_size, current_tile_size=current_tile_size):
                return False

            tile_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = tile_path.with_suffix('.tmp')
            tmp_path.write_bytes(content)
            tmp_path.replace(tile_path)
            meta_path.write_text(content_type or 'image/png', encoding='utf-8')

            with cls._cache_lock:
                cls._disk_usage_bytes = max(0, cls._disk_usage_bytes - current_tile_size + incoming_size)
                cls._last_usage_check_ts = time.time()
            return True
        except Exception as e:
            logger.warning('写入瓦片磁盘缓存失败 %s: %s', tile_path, e)
            return False

    @classmethod
    def _acquire_inflight(cls, key):
        with cls._cache_lock:
            evt = cls._inflight.get(key)
            if evt is None:
                evt = Event()
                cls._inflight[key] = evt
                return evt, True
            return evt, False

    @classmethod
    def _release_inflight(cls, key):
        with cls._cache_lock:
            evt = cls._inflight.pop(key, None)
        if evt:
            evt.set()

    @classmethod
    def _acquire_inflight(cls, key):
        with cls._cache_lock:
            evt = cls._inflight.get(key)
            if evt is None:
                evt = Event()
                cls._inflight[key] = evt
                return evt, True
            return evt, False

    @classmethod
    def _release_inflight(cls, key):
        with cls._cache_lock:
            evt = cls._inflight.pop(key, None)
        if evt:
            evt.set()

    def _fetch(self, request, target_url):
        session = requests.Session()
        session.trust_env = False
        return session.get(
            target_url,
            timeout=(3, 10),
            headers={
                'User-Agent': request.META.get('HTTP_USER_AGENT', 'Mozilla/5.0'),
                'Referer': 'https://www.amap.com/'
            },
            proxies={'http': None, 'https': None}
        )

    def get(self, request):
        x = request.GET.get('x')
        y = request.GET.get('y')
        z = request.GET.get('z')
        style = request.GET.get('style', '6')
        lang = request.GET.get('lang', 'zh_cn')

        if x is None or y is None or z is None:
            return error('x,y,z不能为空', code=400)

        key = self._cache_key(x, y, z, style, lang)

        cached = self._get_from_cache(key)
        if cached:
            response = HttpResponse(cached['content'], content_type=cached['content_type'])
            response['Cache-Control'] = 'public, max-age=300'
            response['X-Map-Cache'] = 'memory-hit'
            return response

        disk_cached = self._get_from_disk_cache(x, y, z, style, lang)
        if disk_cached:
            self._set_cache(key, disk_cached['content'], disk_cached['content_type'])
            response = HttpResponse(disk_cached['content'], content_type=disk_cached['content_type'])
            response['Cache-Control'] = 'public, max-age=300'
            response['X-Map-Cache'] = 'disk-hit'
            return response

        wait_evt, is_owner = self._acquire_inflight(key)
        if not is_owner:
            wait_evt.wait(timeout=8)
            cached_after_wait = self._get_from_cache(key)
            if cached_after_wait:
                response = HttpResponse(cached_after_wait['content'], content_type=cached_after_wait['content_type'])
                response['Cache-Control'] = 'public, max-age=300'
                response['X-Map-Cache'] = 'memory-hit-wait'
                return response

            disk_cached_after_wait = self._get_from_disk_cache(x, y, z, style, lang)
            if disk_cached_after_wait:
                self._set_cache(key, disk_cached_after_wait['content'], disk_cached_after_wait['content_type'])
                response = HttpResponse(disk_cached_after_wait['content'], content_type=disk_cached_after_wait['content_type'])
                response['Cache-Control'] = 'public, max-age=300'
                response['X-Map-Cache'] = 'disk-hit-wait'
                return response

        hosts = [
            'https://webst01.is.autonavi.com',
            'https://webst02.is.autonavi.com',
            'https://webst03.is.autonavi.com',
            'https://webst04.is.autonavi.com'
        ]
        random.shuffle(hosts)

        last_error = None
        try:
            for host in hosts:
                if style == '8':
                    target_url = f'{host}/appmaptile?x={x}&y={y}&z={z}&lang={lang}&style=8'
                else:
                    target_url = f'{host}/appmaptile?x={x}&y={y}&z={z}&style={style}'

                try:
                    resp = self._fetch(request, target_url)
                    if resp.status_code == 200 and resp.content:
                        content_type = resp.headers.get('Content-Type', 'image/png')
                        self._set_cache(key, resp.content, content_type)
                        written = self._set_disk_cache(x, y, z, style, lang, resp.content, content_type)
                        response = HttpResponse(resp.content, content_type=content_type)
                        response['Cache-Control'] = 'public, max-age=1800'
                        response['X-Map-Upstream'] = host
                        response['X-Map-Cache'] = 'miss-disk-write' if written else 'miss-disk-bypass'
                        return response
                    last_error = f'status={resp.status_code}'
                except Exception as e:
                    last_error = str(e)

            logger.warning('地图瓦片代理失败 x=%s y=%s z=%s style=%s err=%s', x, y, z, style, last_error)
            return HttpResponse('地图瓦片代理失败', status=502, content_type='text/plain; charset=utf-8')
        finally:
            if is_owner:
                self._release_inflight(key)
