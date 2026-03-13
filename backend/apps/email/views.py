# -*- coding: utf-8 -*-
from datetime import datetime
import json
import os
import zipfile
from urllib.parse import quote

from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.http import FileResponse

from apps.user.models import User
from utils import token_store, success, error, parse_body, get_param, logger

from .models import EmailAccount, EmailTaskLog, EmailAttachmentLog
from .imap_client import IMAPClient


def _get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        token = request.META.get('HTTP_AUTHORIZATION') or request.GET.get('token')
        info = token_store.get(token)
        if info:
            user_id = info.get('user_id')
    if not user_id:
        return None
    return User.objects.using('default').filter(id=user_id, is_delete=0).first()


def _require_user(request):
    user = _get_current_user(request)
    if not user:
        return None, error('登录状态已失效，请重新登录', code=10016)
    return user, None


def _log_task(user_id, email, action, params, result):
    EmailTaskLog.objects.using('default').create(
        user_id=user_id,
        email=email,
        action=action,
        request_params=json.dumps(params, ensure_ascii=False),
        result=json.dumps(result, ensure_ascii=False)
    )


def _get_imap_config():
    host = getattr(settings, 'EMAIL_IMAP_HOST', 'imap.163.com')
    port = int(getattr(settings, 'EMAIL_IMAP_PORT', 993))
    max_days = int(getattr(settings, 'EMAIL_MAX_QUERY_DAYS', 730))
    return host, port, max_days


def _get_email_account(user_id, email):
    if not email:
        return None
    return EmailAccount.objects.using('default').filter(user_id=user_id, email=email, is_active=1).first()


@method_decorator(csrf_exempt, name='dispatch')
class EmailLoginView(View):
    def post(self, request):
        email = ''
        user = None
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            body = parse_body(request)
            email = (get_param(body, 'email') or '').strip()
            password = get_param(body, 'password') or get_param(body, 'auth_code')
            if not email or not password:
                return error('邮箱或授权码不能为空', code=400)

            host, port, _ = _get_imap_config()
            client = IMAPClient(email, password, imap_server=host, imap_port=port)
            client.login()

            EmailAccount.objects.using('default').update_or_create(
                user_id=user.id,
                email=email,
                defaults={
                    'imap_host': host,
                    'imap_port': port,
                    'auth_code': password,
                    'is_active': 1
                }
            )

            _log_task(user.id, email, 'login', {'email': email}, {'success': True})
            return success(data={'email': email}, msg='登录成功')
        except Exception as e:
            logger.exception('邮箱登录失败: %s', e)
            _log_task(user.id if user else 0, email, 'login', {}, {'success': False, 'error': str(e)})
            return error(str(e), code=400)


@method_decorator(csrf_exempt, name='dispatch')
class EmailListView(View):
    def post(self, request):
        email = ''
        user = None
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            body = parse_body(request)
            email = (get_param(body, 'email') or '').strip()
            start_date = get_param(body, 'start_date')
            end_date = get_param(body, 'end_date')
            page = int(get_param(body, 'page', 1) or 1)
            page_size = int(get_param(body, 'page_size', 20) or 20)

            account = _get_email_account(user.id, email)
            if not account:
                return error('请先登录邮箱', code=400)

            if not start_date or not end_date:
                return error('开始/结束日期不能为空', code=400)

            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            except Exception:
                return error('日期格式不正确', code=400)

            host, port, max_days = _get_imap_config()
            if (end_dt - start_dt).days > max_days:
                return error(f'查询范围不能超过 {max_days} 天', code=400)

            client = IMAPClient(account.email, account.auth_code, imap_server=host, imap_port=port)
            client.login()
            data = client.fetch_emails(start_dt, end_dt, page, page_size)

            _log_task(user.id, email, 'query', {'start_date': start_date, 'end_date': end_date, 'page': page, 'page_size': page_size}, {'total': data.get('total', 0)})
            return success(data=data)
        except Exception as e:
            logger.exception('邮箱查询失败: %s', e)
            _log_task(user.id if user else 0, email, 'query', {}, {'error': str(e)})
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class EmailDetailView(View):
    def post(self, request):
        email = ''
        user = None
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            body = parse_body(request)
            email = (get_param(body, 'email') or '').strip()
            email_id = get_param(body, 'email_id')
            if not email or not email_id:
                return error('邮箱或邮件ID不能为空', code=400)

            account = _get_email_account(user.id, email)
            if not account:
                return error('请先登录邮箱', code=400)

            host, port, _ = _get_imap_config()
            client = IMAPClient(account.email, account.auth_code, imap_server=host, imap_port=port)
            client.login()
            content = client.fetch_email_content(email_id)

            _log_task(user.id, email, 'detail', {'email_id': email_id}, {'success': True})
            return success(data={'content': content})
        except Exception as e:
            logger.exception('邮件正文获取失败: %s', e)
            _log_task(user.id if user else 0, email, 'detail', {}, {'error': str(e)})
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class EmailDownloadView(View):
    def post(self, request):
        email = ''
        user = None
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            body = parse_body(request)
            email = (get_param(body, 'email') or '').strip()
            email_ids = body.get('email_ids') or []
            if isinstance(email_ids, str):
                email_ids = [email_ids]

            account = _get_email_account(user.id, email)
            if not account:
                return error('请先登录邮箱', code=400)

            if not email_ids:
                return error('请提供要下载的邮件ID', code=400)

            host, port, _ = _get_imap_config()
            client = IMAPClient(account.email, account.auth_code, imap_server=host, imap_port=port)
            client.login()
            stats, attachments = client.download_attachments_async(email_ids)

            if attachments:
                EmailAttachmentLog.objects.using('default').bulk_create([
                    EmailAttachmentLog(
                        user_id=user.id,
                        email=email,
                        email_id='*',
                        subject=item.get('subject', ''),
                        folder_name=item.get('folder_name', ''),
                        file_name=item.get('file_name', ''),
                        status=item.get('status', 'success')
                    ) for item in attachments
                ], batch_size=200)

            _log_task(user.id, email, 'download', {'count': len(email_ids)}, stats)
            return success(data={'stats': stats})
        except Exception as e:
            logger.exception('附件下载失败: %s', e)
            _log_task(user.id if user else 0, email, 'download', {}, {'error': str(e)})
            return error(str(e), code=500)


def _ensure_download_dir():
    base_dir = getattr(settings, 'EMAIL_ATTACHMENT_DIR', 'downloads')
    if os.path.isabs(base_dir):
        download_dir = base_dir
    else:
        download_dir = os.path.join(getattr(settings, 'BASE_DIR', ''), base_dir)
    os.makedirs(download_dir, exist_ok=True)
    return download_dir


def _zip_directories(dir_paths, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for dir_path in dir_paths:
            if not os.path.exists(dir_path):
                continue
            for root, _, files in os.walk(dir_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    rel_path = os.path.relpath(file_path, os.path.dirname(dir_path))
                    zf.write(file_path, rel_path)


@method_decorator(csrf_exempt, name='dispatch')
class EmailDeleteDownloadedView(View):
    def post(self, request):
        email = ''
        user = None
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            body = parse_body(request)
            email = (get_param(body, 'email') or '').strip()
            email_ids = body.get('email_ids') or []
            if isinstance(email_ids, str):
                email_ids = [email_ids]

            account = _get_email_account(user.id, email)
            if not account:
                return error('请先登录邮箱', code=400)

            if not email_ids:
                return error('请提供要删除的邮件ID', code=400)

            host, port, _ = _get_imap_config()
            client = IMAPClient(account.email, account.auth_code, imap_server=host, imap_port=port)
            client.login()
            stats = client.delete_downloaded_emails(email_ids)

            _log_task(user.id, email, 'delete', {'count': len(email_ids)}, stats)
            return success(data={'results': stats})
        except Exception as e:
            logger.exception('删除已下载邮件失败: %s', e)
            _log_task(user.id if user else 0, email, 'delete', {}, {'error': str(e)})
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class EmailDownloadPackageView(View):
    def post(self, request):
        email = ''
        user = None
        try:
            user, auth_err = _require_user(request)
            if auth_err:
                return auth_err

            body = parse_body(request)
            email = (get_param(body, 'email') or '').strip()
            email_ids = body.get('email_ids') or []
            if isinstance(email_ids, str):
                email_ids = [email_ids]

            account = _get_email_account(user.id, email)
            if not account:
                return error('请先登录邮箱', code=400)

            if not email_ids:
                return error('请提供要下载的邮件ID', code=400)

            host, port, _ = _get_imap_config()
            client = IMAPClient(account.email, account.auth_code, imap_server=host, imap_port=port)
            client.login()
            stats, attachments = client.download_attachments_async(email_ids)

            folder_names = list({item.get('folder_name') for item in attachments if item.get('folder_name')})
            if not folder_names:
                return error('未找到可打包的附件目录', code=400)

            download_dir = _ensure_download_dir()
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            zip_name = f'attachments_{ts}.zip'
            zip_path = os.path.join(download_dir, zip_name)

            dir_paths = [os.path.join(download_dir, folder) for folder in folder_names]
            _zip_directories(dir_paths, zip_path)

            if os.path.getsize(zip_path) == 0:
                try:
                    os.remove(zip_path)
                except Exception:
                    pass
                return error('附件打包为空，请确认已成功下载附件', code=400)

            if attachments:
                EmailAttachmentLog.objects.using('default').bulk_create([
                    EmailAttachmentLog(
                        user_id=user.id,
                        email=email,
                        email_id='*',
                        subject=item.get('subject', ''),
                        folder_name=item.get('folder_name', ''),
                        file_name=item.get('file_name', ''),
                        status=item.get('status', 'success')
                    ) for item in attachments
                ], batch_size=200)

            _log_task(user.id, email, 'download', {'count': len(email_ids)}, stats)

            response = FileResponse(open(zip_path, 'rb'), as_attachment=True)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(zip_name)}"
            return response
        except Exception as e:
            logger.exception('附件打包下载失败: %s', e)
            _log_task(user.id if user else 0, email, 'download', {}, {'error': str(e)})
            return error(str(e), code=500)
