# -*- coding: utf-8 -*-
from datetime import datetime
import socket
import re

from django.db import connections
from django.views import View
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from apps.user.models import User
from utils import success, error, token_store, logger

RAW_DB = 'default'
RAW_SCHEMA = 'jdhydevicedb'


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


def _require_user(request):
    user = _get_current_user(request)
    if not user:
        return None, error('登录状态已失效，请重新登录', code=10016)
    return user, None


def _get_int_query(request, key, default):
    return int(request.GET.get(key, default))


def _to_naive(dt):
    if not dt:
        return None
    if timezone.is_aware(dt):
        return timezone.localtime(dt).replace(tzinfo=None)
    return dt


def _parse_date_range(start_date, end_date):
    now = timezone.localtime(timezone.now())
    if not start_date or not end_date:
        start = datetime(now.year, 1, 1, 0, 0, 0)
        end = datetime(now.year, 12, 31, 23, 59, 59)
        return start, end
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        if start > end:
            start, end = end, start
        return start, end
    except Exception:
        start = datetime(now.year, 1, 1, 0, 0, 0)
        end = datetime(now.year, 12, 31, 23, 59, 59)
        return start, end


def _dict_fetch_all(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@method_decorator(csrf_exempt, name='dispatch')
class ReceiveLogListView(View):
    def get(self, request):
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            page = _get_int_query(request, 'page', 1)
            page_size = _get_int_query(request, 'page_size', 10)
            keyword = (request.GET.get('keyword') or '').strip()
            ingest_filter = (request.GET.get('stage') or '').strip().lower()
            start_date = (request.GET.get('start_date') or '').strip()
            end_date = (request.GET.get('end_date') or '').strip()

            start_dt, end_dt = _parse_date_range(start_date, end_date)

            where = ["1=1"]
            params = []

            where.append("(time IS NULL OR (time BETWEEN %s AND %s))")
            params.extend([start_dt, end_dt])

            if keyword:
                like_kw = f"%{keyword}%"
                where.append("(device_id LIKE %s OR iridiumid LIKE %s OR sensorflag LIKE %s OR raw LIKE %s OR ip LIKE %s)")
                params.extend([like_kw, like_kw, like_kw, like_kw, like_kw])

            if ingest_filter in ['received', 'parsed', 'db_saved', 'completed', 'recv_failed', 'parse_failed', 'db_failed']:
                where.append("result=%s")
                params.append(ingest_filter)

            where_sql = " AND ".join(where)

            count_sql = f"SELECT COUNT(*) FROM `t_receive_log` WHERE {where_sql}"
            data_sql = (
                f"SELECT id, ip, time, device_id, iridiumid, sn, sensorflag, packet_len, result, message, raw, parse_result "
                f"FROM `t_receive_log` WHERE {where_sql} ORDER BY id DESC"
            )

            with connections[RAW_DB].cursor() as cursor:
                cursor.execute(count_sql, params)
                total = cursor.fetchone()[0]

                cursor.execute(data_sql, params)
                rows = _dict_fetch_all(cursor)

            paginator = Paginator(rows, page_size)
            page_obj = paginator.get_page(page)

            records = []
            for row in page_obj:
                records.append({
                    'id': row.get('id'),
                    'ip': row.get('ip') or '',
                    'time': row.get('time').strftime('%Y-%m-%d %H:%M:%S') if row.get('time') else '',
                    'device_id': row.get('device_id') or '',
                    'iridiumid': row.get('iridiumid') or '',
                    'sn': row.get('sn') or 0,
                    'sensorflag': row.get('sensorflag') or '',
                    'packet_len': row.get('packet_len') or 0,
                    'result': row.get('result') or 'recv_failed',
                    'stage': row.get('result') or '',
                    'message': row.get('message') or '',
                    'raw': row.get('raw') or '',
                    'parse_result': row.get('parse_result') or ''
                })

            return success(data={
                'total': total,
                'page': page,
                'page_size': page_size,
                'records': records
            })
        except Exception as e:
            logger.exception('数据接收记录异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class ReceiveLogSendTCPView(View):
    def post(self, request):
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            try:
                body = (request.body or b'').decode('utf-8')
            except Exception:
                body = ''

            host = ''
            port = 0
            packets = []
            if body:
                try:
                    import json
                    payload = json.loads(body)
                except Exception:
                    payload = {}
            else:
                payload = {}

            host = (payload.get('host') or '').strip()
            port = int(payload.get('port') or 0)
            packets = payload.get('packets') or []

            if not host or not port:
                return error('目标地址或端口不能为空', code=400)
            if not isinstance(packets, list) or not packets:
                return error('请提供要发送的数据', code=400)

            cleaned_packets = []
            for raw in packets:
                text = re.sub(r'[^0-9a-fA-F]', '', str(raw))
                if not text:
                    continue
                if len(text) % 2 != 0:
                    return error('十六进制长度必须为偶数', code=400)
                cleaned_packets.append(text)

            if not cleaned_packets:
                return error('未解析到有效数据', code=400)

            sent = 0
            with socket.create_connection((host, port), timeout=3) as sock:
                for hex_str in cleaned_packets:
                    sock.sendall(bytes.fromhex(hex_str))
                    sent += 1

            return success(msg=f'发送完成，共发送 {sent} 条')
        except Exception as e:
            logger.exception('发送TCP测试数据异常: %s', e)
            return error(str(e), code=500)
