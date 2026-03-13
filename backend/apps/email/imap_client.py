# -*- coding: utf-8 -*-
import imaplib
import email
import os
import re
import time
import threading
from datetime import timedelta
from email.header import decode_header
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup
from django.conf import settings

from utils import logger

_attachment_dir_setting = getattr(settings, 'EMAIL_ATTACHMENT_DIR', 'downloads')
if os.path.isabs(_attachment_dir_setting):
    ATTACHMENT_BASE_DIR = _attachment_dir_setting
else:
    ATTACHMENT_BASE_DIR = os.path.join(getattr(settings, 'BASE_DIR', ''), _attachment_dir_setting)
MAX_DOWNLOAD_WORKERS = int(getattr(settings, 'EMAIL_MAX_WORKERS', 16))
DOWNLOAD_RETRY_TIMES = int(getattr(settings, 'EMAIL_DOWNLOAD_RETRY_TIMES', 3))
IMAP_TIMEOUT = int(getattr(settings, 'EMAIL_IMAP_TIMEOUT', 30))


class IMAPClient:
    def __init__(self, email_user, email_pwd, imap_server='imap.163.com', imap_port=993):
        self.user = email_user
        self.pwd = email_pwd
        self.server = imap_server
        self.port = imap_port
        self.conn = None

    def login(self):
        try:
            self.conn = imaplib.IMAP4_SSL(self.server, self.port, timeout=IMAP_TIMEOUT)
        except TypeError:
            self.conn = imaplib.IMAP4_SSL(self.server, self.port)

        self.conn.login(self.user, self.pwd)

        imaplib.Commands['ID'] = 'AUTH'
        args = ("name", "client", "contact", self.user, "version", "1.0", "vendor", "email_pro")
        self.conn._simple_command('ID', '("' + '" "'.join(args) + '")')

        logger.info('%s 登录成功', self.user)

    def ensure_connection(self):
        try:
            self.conn.noop()
        except Exception:
            logger.warning('IMAP 断线，重新连接')
            self.login()

    def decode_str(self, s):
        if not s:
            return ''
        parts = decode_header(s)
        out = ''
        for text, enc in parts:
            if isinstance(text, bytes):
                out += text.decode(enc or 'utf-8', errors='ignore')
            else:
                out += text
        return out

    def extract_folder_name_from_subject(self, subject: str):
        if not subject or not subject[-1].isdigit():
            return None
        m = re.search(r'(\d+)$', subject)
        return m.group(1) if m else None

    def fetch_emails(self, start_date, end_date, page, page_size):
        self.ensure_connection()
        self.conn.select('INBOX')

        criteria = ['ALL']
        criteria.append(f'SINCE "{start_date.strftime("%d-%b-%Y")}"')
        criteria.append(f'BEFORE "{(end_date + timedelta(days=1)).strftime("%d-%b-%Y")}"')

        typ, data = self.conn.search(None, *criteria)
        if typ != 'OK':
            raise Exception('邮件搜索失败')

        email_ids = list(reversed(data[0].split()))
        total = len(email_ids)

        all_ids = [eid.decode() for eid in email_ids]

        start = (page - 1) * page_size
        end = start + page_size
        page_ids = email_ids[start:end]

        emails = []
        for eid in page_ids:
            typ, msg_data = self.conn.fetch(eid, '(BODY.PEEK[HEADER])')
            if typ != 'OK':
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            emails.append({
                'id': eid.decode(),
                'subject': self.decode_str(msg.get('subject')),
                'from': self.decode_str(msg.get('from')),
                'date': msg.get('date') or '',
                'content': '',
                'attachments': []
            })

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'emails': emails,
            'all_ids': all_ids
        }

    def download_attachments_async(self, email_ids: list):
        stats = {
            'success_emails': 0,
            'failed_emails': 0,
            'skipped_emails': 0,
            'success_attachments': 0,
            'skipped_attachments': 0,
        }
        attachment_logs = []
        lock = threading.Lock()

        def _record_attachment(folder_name, subject, file_name, status):
            with lock:
                attachment_logs.append({
                    'folder_name': folder_name,
                    'subject': subject,
                    'file_name': file_name,
                    'status': status
                })

        def _download_one_email(eid: str):
            for attempt in range(DOWNLOAD_RETRY_TIMES):
                conn = None
                try:
                    try:
                        conn = imaplib.IMAP4_SSL(self.server, self.port, timeout=IMAP_TIMEOUT)
                    except TypeError:
                        conn = imaplib.IMAP4_SSL(self.server, self.port)

                    conn.login(self.user, self.pwd)

                    imaplib.Commands['ID'] = 'AUTH'
                    args = ("name", "client", "contact", self.user, "version", "1.0", "vendor", "email_pro")
                    conn._simple_command('ID', '("' + '" "'.join(args) + '")')

                    conn.select('INBOX')
                    typ, msg_data = conn.fetch(eid.encode(), '(RFC822)')
                    if typ != 'OK':
                        raise Exception('FETCH FAILED')

                    msg = email.message_from_bytes(msg_data[0][1])
                    subject = self.decode_str(msg.get('subject', ''))

                    folder_name = self.extract_folder_name_from_subject(subject)
                    if not folder_name:
                        with lock:
                            stats['skipped_emails'] += 1
                        return

                    target_dir = os.path.join(ATTACHMENT_BASE_DIR, folder_name)
                    os.makedirs(target_dir, exist_ok=True)

                    for part in msg.walk():
                        fname = part.get_filename()
                        if not fname:
                            continue

                        fname = self.decode_str(fname).strip()
                        file_path = os.path.join(target_dir, fname)

                        if os.path.exists(file_path):
                            logger.warning('跳过同名附件：目录 [%s] 已存在文件 [%s]', folder_name, fname)
                            with lock:
                                stats['skipped_attachments'] += 1
                            _record_attachment(folder_name, subject, fname, 'skip')
                            continue

                        data = part.get_payload(decode=True)
                        if not data:
                            continue

                        with open(file_path, 'wb') as f:
                            f.write(data)

                        logger.info('已下载附件：目录 [%s] 文件 [%s]', folder_name, fname)

                        with lock:
                            stats['success_attachments'] += 1
                        _record_attachment(folder_name, subject, fname, 'success')

                    with lock:
                        stats['success_emails'] += 1
                    return

                except Exception as e:
                    if attempt < DOWNLOAD_RETRY_TIMES - 1:
                        time.sleep(1)
                        continue

                    logger.error('邮件 %s 下载失败：%s', eid, e)
                    with lock:
                        stats['failed_emails'] += 1
                    return

                finally:
                    try:
                        if conn:
                            conn.logout()
                    except Exception:
                        pass

        logger.info('开始下载附件，共 %s 封邮件', len(email_ids))

        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as pool:
            futures = [pool.submit(_download_one_email, eid) for eid in email_ids]
            for _ in as_completed(futures):
                pass

        logger.info(
            '下载完成：成功邮件 %s，失败邮件 %s，跳过邮件 %s，成功附件 %s，跳过附件 %s',
            stats['success_emails'], stats['failed_emails'], stats['skipped_emails'],
            stats['success_attachments'], stats['skipped_attachments']
        )

        return stats, attachment_logs

    def fetch_email_content(self, eid):
        self.ensure_connection()
        self.conn.select('INBOX')

        typ, msg_data = self.conn.fetch(eid, '(RFC822)')
        if typ != 'OK':
            raise Exception('邮件获取失败')

        msg = email.message_from_bytes(msg_data[0][1])
        content = ''

        for part in msg.walk():
            if part.is_multipart():
                continue

            ctype = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue

            try:
                if ctype == 'text/plain':
                    content = payload.decode(errors='ignore')
                    break
                elif ctype == 'text/html':
                    soup = BeautifulSoup(payload.decode(errors='ignore'), 'html.parser')
                    content = soup.get_text('\n', strip=True)
            except Exception:
                continue

        return content

    def delete_downloaded_emails(self, email_ids: list):
        stats = {
            'deleted': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }

        lock = threading.Lock()

        def _delete_one_email(eid: str):
            conn = None
            try:
                try:
                    conn = imaplib.IMAP4_SSL(self.server, self.port, timeout=IMAP_TIMEOUT)
                except TypeError:
                    conn = imaplib.IMAP4_SSL(self.server, self.port)

                conn.login(self.user, self.pwd)

                imaplib.Commands['ID'] = 'AUTH'
                args = ("name", "client", "contact", self.user, "version", "1.0", "vendor", "email_pro")
                conn._simple_command('ID', '("' + '" "'.join(args) + '")')

                conn.select('INBOX')

                typ, msg_data = conn.fetch(eid.encode(), '(BODY.PEEK[HEADER])')
                if typ != 'OK':
                    raise Exception('FETCH HEADER FAILED')

                msg = email.message_from_bytes(msg_data[0][1])
                subject = self.decode_str(msg.get('subject', ''))
                folder_name = self.extract_folder_name_from_subject(subject)

                if not folder_name:
                    logger.info('跳过删除：邮件 %s 主题无编号', eid)
                    with lock:
                        stats['skipped'] += 1
                    return

                target_dir = os.path.join(ATTACHMENT_BASE_DIR, folder_name)

                if not os.path.exists(target_dir):
                    logger.info('跳过删除：邮件 %s 目录不存在 [%s]', eid, folder_name)
                    with lock:
                        stats['skipped'] += 1
                    return

                if not os.listdir(target_dir):
                    logger.info('跳过删除：邮件 %s 目录为空 [%s]', eid, folder_name)
                    with lock:
                        stats['skipped'] += 1
                    return

                conn.store(eid.encode(), '+FLAGS', '\\Deleted')
                conn.expunge()

                logger.info('已删除邮件：%s（附件目录 [%s]）', eid, folder_name)

                with lock:
                    stats['deleted'] += 1

            except Exception as e:
                logger.error('删除邮件失败：%s，错误：%s', eid, e)
                with lock:
                    stats['failed'] += 1
                    stats['errors'].append(f'{eid}: {str(e)}')

            finally:
                try:
                    if conn:
                        conn.logout()
                except Exception:
                    pass

        logger.info('开始删除邮件，共 %s 封', len(email_ids))

        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as pool:
            futures = [pool.submit(_delete_one_email, eid) for eid in email_ids]
            for _ in as_completed(futures):
                pass

        logger.info('删除完成：成功 %s，跳过 %s，失败 %s', stats['deleted'], stats['skipped'], stats['failed'])

        return stats
