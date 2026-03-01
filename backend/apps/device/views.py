# -*- coding: utf-8 -*-
"""
设备视图（只读展示模式）
- 用户权限：test.t_user
- 设备/业务数据：jdhydevicedb 原始库
"""
from datetime import datetime

from django.db import connections
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.utils import timezone

from apps.user.models import User
from utils import success, error, logger, token_store

RAW_DB = 'raw'
RAW_SCHEMA = 'jdhydevicedb'
TABLE_03001 = '03001idb_icedriftbuoy'
TABLE_03004 = '03004imb_icemassbalancebuoy'


def _get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        token = request.META.get('HTTP_AUTHORIZATION') or request.GET.get('token')
        info = token_store.get(token)
        if info:
            user_id = info.get('user_id')
    if not user_id:
        return None
    return User.objects.filter(id=user_id, is_delete=0).first()


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


def _device_type_from_sensorflag(sensorflag):
    flag = (sensorflag or '').lower()
    return 'station' if ('station' in flag or 'aws' in flag) else 'buoy'


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


def _field_label(field, comment_map):
    c = (comment_map.get(field) or '').strip()
    return c if c else field


def _get_latest_time_map(device_ids):
    if not device_ids:
        return {}
    placeholders = ','.join(['%s'] * len(device_ids))
    sql = f"""
    SELECT devid, MAX(packet_time) AS latest_time
    FROM (
      SELECT devid, `time` AS packet_time FROM `{TABLE_03001}` WHERE devid IN ({placeholders})
      UNION ALL
      SELECT devid, `time` AS packet_time FROM `{TABLE_03004}` WHERE devid IN ({placeholders})
    ) t
    GROUP BY devid
    """
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(sql, device_ids + device_ids)
        rows = cursor.fetchall()
    return {r[0]: r[1] for r in rows}


def _get_latest_row_by_device(table_name, device_id):
    with connections[RAW_DB].cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM `{table_name}` WHERE devid=%s AND `time` IS NOT NULL ORDER BY `time` DESC LIMIT 1",
            [device_id]
        )
        return _dict_fetch_one(cursor)


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

            sql = """
            SELECT id, devid, name, iridiumid, sensorflag, latflag, lat, lonflag, lon, workstate, display, ownership
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
                raw_id, devid, name, iridiumid, sensorflag, latflag, lat, lonflag, lon, workstate, display_flag, own = row
                nlat, nlon = _normalize_lat_lon(lat, lon, latflag, lonflag)
                raw_list.append({
                    'id': int(raw_id) if raw_id is not None else 0,
                    'device_id': devid,
                    'device_name': name or devid,
                    'iridium_id': iridiumid or '',
                    'sensorflag': sensorflag or '',
                    'ownership': own or '',
                    'latitude': nlat,
                    'longitude': nlon,
                    'workstate': int(workstate) if workstate is not None else None,
                    'display': int(display_flag) if display_flag is not None else None,
                    'device_type': _device_type_from_sensorflag(sensorflag),
                })

            if ownership:
                raw_list = [x for x in raw_list if ownership in x['ownership']]

            latest_map = _get_latest_time_map([x['device_id'] for x in raw_list])
            for x in raw_list:
                t = latest_map.get(x['device_id'])
                x['status'] = 1 if _is_online_time(t) else 0
                x['status_name'] = '在线' if x['status'] == 1 else '离线'
                x['last_report_time'] = _fmt_dt(t)

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

            row_03001 = _get_latest_row_by_device(TABLE_03001, device_id)
            row_03004 = _get_latest_row_by_device(TABLE_03004, device_id)

            latest_row = None
            source_table = ''
            if row_03001 and row_03004:
                t1 = _to_naive(row_03001.get('time'))
                t2 = _to_naive(row_03004.get('time'))
                if t2 and (not t1 or t2 >= t1):
                    latest_row = row_03004
                    source_table = TABLE_03004
                else:
                    latest_row = row_03001
                    source_table = TABLE_03001
            elif row_03001:
                latest_row = row_03001
                source_table = TABLE_03001
            elif row_03004:
                latest_row = row_03004
                source_table = TABLE_03004

            if not latest_row:
                return success(data={'device_id': device_id, 'latest': None, 'field_list': []})

            comment_map = _get_comment_map(source_table)
            field_list = []
            for k, v in latest_row.items():
                if k in ['id', 'devid']:
                    continue
                if k == 'time':
                    v = _fmt_dt(v)
                field_list.append({'field': k, 'label': _field_label(k, comment_map), 'value': v})

            lat, lon = _normalize_lat_lon(latest_row.get('lat'), latest_row.get('lon'), latest_row.get('latflag'), latest_row.get('lonflag'))
            latest = {
                'packet_time': _fmt_dt(latest_row.get('time')),
                'latitude': lat,
                'longitude': lon,
                'board_voltage': latest_row.get('board_voltage'),
                'board_temp': latest_row.get('board_temp'),
                'air_temp': latest_row.get('air_temp'),
                'air_humid': latest_row.get('air_humid'),
                'atmosphere': latest_row.get('atmosphere'),
                'wind_speed': latest_row.get('wind_speed'),
                'wind_direct': latest_row.get('wind_direct')
            }

            return success(data={
                'device_id': device_id,
                'source_table': source_table,
                'latest': latest,
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

            comment_03001 = _get_comment_map(TABLE_03001)
            comment_03004 = _get_comment_map(TABLE_03004)

            fields = [
                'time', 'sn', 'iridiumid', 'latflag', 'lat', 'lonflag', 'lon',
                'board_voltage', 'board_temp', 'air_temp', 'air_humid', 'atmosphere',
                'wind_speed', 'wind_direct', 'bd_time', 'bd_posflag', 'bd_latflag',
                'bd_lat', 'bd_lonflag', 'bd_lon', 'tempC150', 'tempC200_1',
                'tempC200_2', 'tempC_pt', 'sonar_on', 'sonar_under', 'uploaded'
            ]

            columns = []
            for f in fields:
                label = _field_label(f, comment_03004 if f in comment_03004 else comment_03001)
                columns.append({'field': f, 'label': label})

            count_sql = f"""
            SELECT COUNT(*) FROM (
                SELECT `time` AS packet_time FROM `{TABLE_03001}` WHERE devid=%s AND `time` BETWEEN %s AND %s
                UNION ALL
                SELECT `time` AS packet_time FROM `{TABLE_03004}` WHERE devid=%s AND `time` BETWEEN %s AND %s
            ) x
            """

            data_sql = f"""
            SELECT * FROM (
                SELECT '{TABLE_03001}' AS source_table,
                       `time`, sn, iridiumid, latflag, lat, lonflag, lon,
                       board_voltage, board_temp,
                       NULL AS air_temp, NULL AS air_humid, atmosphere,
                       NULL AS wind_speed, NULL AS wind_direct,
                       bd_time, bd_posflag, bd_latflag, bd_lat, bd_lonflag, bd_lon,
                       NULL AS tempC150, NULL AS tempC200_1, NULL AS tempC200_2, NULL AS tempC_pt,
                       NULL AS sonar_on, NULL AS sonar_under,
                       uploaded
                FROM `{TABLE_03001}`
                WHERE devid=%s AND `time` BETWEEN %s AND %s

                UNION ALL

                SELECT '{TABLE_03004}' AS source_table,
                       `time`, sn, iridiumid, latflag, lat, lonflag, lon,
                       board_voltage, board_temp,
                       air_temp, air_humid, atmosphere,
                       wind_speed, wind_direct,
                       bd_time, bd_posflag, bd_latflag, bd_lat, bd_lonflag, bd_lon,
                       tempC150, tempC200_1, tempC200_2, tempC_pt,
                       sonar_on, sonar_under,
                       uploaded
                FROM `{TABLE_03004}`
                WHERE devid=%s AND `time` BETWEEN %s AND %s
            ) t
            ORDER BY `time` ASC
            LIMIT %s OFFSET %s
            """

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(count_sql, [device_id, start_dt, end_dt, device_id, start_dt, end_dt])
                total_count = cursor.fetchone()[0]

                cursor.execute(data_sql, [device_id, start_dt, end_dt, device_id, start_dt, end_dt, page_size, offset])
                rows = _dict_fetch_all(cursor)

            points = []
            for r in rows:
                item = {
                    'time': _fmt_dt(r.get('time')),
                    'source_table': r.get('source_table')
                }
                for f in fields:
                    item[f] = r.get(f)
                points.append(item)

            return success(data={
                'device_id': device_id,
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
            limit = int(request.GET.get('limit', 200))
            if not device_id:
                return error('device_id不能为空', code=400)
            if user.type != 1 and device_id not in (user.device_list or []):
                return error('设备不存在或无权限', code=404)

            sql = f"""
            SELECT packet_time, latflag, lat, lonflag, lon FROM (
                SELECT `time` AS packet_time, latflag, lat, lonflag, lon FROM `{TABLE_03001}` WHERE devid = %s
                UNION ALL
                SELECT `time` AS packet_time, latflag, lat, lonflag, lon FROM `{TABLE_03004}` WHERE devid = %s
            ) t
            WHERE lat IS NOT NULL AND lon IS NOT NULL AND packet_time IS NOT NULL
            ORDER BY packet_time DESC
            LIMIT %s
            """
            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(sql, [device_id, device_id, limit])
                rows = cursor.fetchall()

            points = []
            for r in reversed(rows):
                lat, lon = _normalize_lat_lon(r[2], r[4], r[1], r[3])
                if lat is None or lon is None:
                    continue
                points.append({'time': _fmt_dt(r[0]), 'lat': lat, 'lng': lon})

            return success(data={'device_id': device_id, 'point_count': len(points), 'points': points})
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

            sql = "SELECT devid, sensorflag, ownership FROM `device_list`"
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
                dt = _device_type_from_sensorflag(d[1])
                own = (d[2] or '')
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
            total_users = User.objects.filter(is_delete=0).count() if user.type == 1 else 1

            with connections[RAW_DB].cursor() as cursor:
                if devids:
                    placeholders = ','.join(['%s'] * len(devids))
                    cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_03001}` WHERE devid IN ({placeholders})", devids)
                    c1 = cursor.fetchone()[0]
                    cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_03004}` WHERE devid IN ({placeholders})", devids)
                    c2 = cursor.fetchone()[0]
                    cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_03001}` WHERE devid IN ({placeholders}) AND lat IS NOT NULL AND lon IS NOT NULL", devids)
                    p1 = cursor.fetchone()[0]
                    cursor.execute(f"SELECT COUNT(*) FROM `{TABLE_03004}` WHERE devid IN ({placeholders}) AND lat IS NOT NULL AND lon IS NOT NULL", devids)
                    p2 = cursor.fetchone()[0]
                    cursor.execute(f"SELECT MAX(t) FROM (SELECT MAX(`time`) AS t FROM `{TABLE_03001}` WHERE devid IN ({placeholders}) UNION ALL SELECT MAX(`time`) AS t FROM `{TABLE_03004}` WHERE devid IN ({placeholders})) x", devids + devids)
                    latest_packet = cursor.fetchone()[0]
                else:
                    c1 = c2 = p1 = p2 = 0
                    latest_packet = None

            total_packets = c1 + c2
            valid_packets = p1 + p2

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
