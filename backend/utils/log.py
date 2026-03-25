# -*- coding: utf-8 -*-
"""
企业级日志配置：
- 统一格式（含进程/线程）
- 业务日志：logs/info.log
- 错误日志：logs/error.log
- 接收服务请求日志：logs/collect_data_requests.log
- 单文件 500MB 自动滚动
- 超过 1GB 的日志文件自动 gzip 压缩
- 日志文件保留 7 天
"""
import gzip
import logging
import re
import shutil
import socket
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

HOSTNAME = socket.gethostname()
_REQUEST_ID_CTX = ContextVar('request_id', default='-')


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _REQUEST_ID_CTX.get()
        return True


LOG_FORMAT = (
    '%(asctime)s [%(levelname)s] %(name)s '
    '[host=' + HOSTNAME + ' pid=%(process)d tid=%(thread)d rid=%(request_id)s] %(message)s'
)
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

MAX_FILE_BYTES = 500 * 1024 * 1024
COMPRESS_THRESHOLD_BYTES = 1024 * 1024 * 1024
RETENTION_DAYS = 7
BACKUP_COUNT = 30


def set_request_id(request_id: str) -> None:
    _REQUEST_ID_CTX.set(request_id or '-')


def clear_request_id() -> None:
    _REQUEST_ID_CTX.set('-')


def new_request_id() -> str:
    return uuid.uuid4().hex


class _LevelFilter(logging.Filter):
    def __init__(self, low: int, high: int):
        super().__init__()
        self.low = low
        self.high = high

    def filter(self, record: logging.LogRecord) -> bool:
        return self.low <= record.levelno <= self.high


def _cleanup_old_logs(prefix: str, days: int = RETENTION_DAYS) -> None:
    cutoff = datetime.now() - timedelta(days=days)
    for path in LOG_DIR.glob(f'{prefix}*'):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                path.unlink(missing_ok=True)
        except FileNotFoundError:
            continue


def _gzip_file(path: Path) -> None:
    gz_path = Path(f'{path}.gz')
    with open(path, 'rb') as src, gzip.open(gz_path, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    path.unlink(missing_ok=True)


def _compress_large_logs(prefix: str, threshold: int = COMPRESS_THRESHOLD_BYTES) -> None:
    escaped = re.escape(prefix)
    pattern = re.compile(rf'^{escaped}(\.\d+)?$')
    for path in LOG_DIR.glob(f'{prefix}*'):
        if path.is_file() and pattern.match(path.name):
            try:
                if path.stat().st_size > threshold:
                    _gzip_file(path)
            except FileNotFoundError:
                continue


def _build_rotating_handler(file_name: str) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        LOG_DIR / file_name,
        maxBytes=MAX_FILE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    handler.addFilter(_RequestIdFilter())
    return handler


def _init_file_lifecycle() -> None:
    for prefix in ('info.log', 'error.log', 'collect_data_requests.log'):
        _compress_large_logs(prefix)
        _cleanup_old_logs(prefix)


_init_file_lifecycle()


logger = logging.getLogger('monitor')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    logger.propagate = False

    info_handler = _build_rotating_handler('info.log')
    info_handler.addFilter(_LevelFilter(logging.INFO, logging.WARNING))

    error_handler = _build_rotating_handler('error.log')
    error_handler.setLevel(logging.ERROR)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    stream_handler.addFilter(_RequestIdFilter())

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(stream_handler)


request_logger = logging.getLogger('collect_data.request')
if not request_logger.handlers:
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False

    request_file_handler = _build_rotating_handler('collect_data_requests.log')
    request_stream_handler = logging.StreamHandler(sys.stdout)
    request_stream_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    request_stream_handler.addFilter(_RequestIdFilter())

    request_logger.addHandler(request_file_handler)
    request_logger.addHandler(request_stream_handler)
