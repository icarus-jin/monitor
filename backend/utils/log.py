# -*- coding: utf-8 -*-
"""
日志工具
- 统一日志格式
- 支持请求、异常、业务操作记录
"""
import logging
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def _cleanup_old_logs(prefix: str, days: int = 30) -> None:
    cutoff = datetime.now() - timedelta(days=days)
    for path in LOG_DIR.glob(f'{prefix}*'):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                path.unlink(missing_ok=True)
        except FileNotFoundError:
            continue


logger = logging.getLogger('monitor')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(stream_handler)


request_logger = logging.getLogger('collect_data.request')
if not request_logger.handlers:
    request_logger.setLevel(logging.INFO)
    request_log_path = LOG_DIR / 'collect_data_requests.log'
    file_handler = RotatingFileHandler(
        request_log_path,
        maxBytes=1024 * 1024 * 1024,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    request_logger.addHandler(file_handler)
    request_logger.addHandler(logging.StreamHandler(sys.stdout))
    request_logger.propagate = False
    _cleanup_old_logs('collect_data_requests.log', days=30)