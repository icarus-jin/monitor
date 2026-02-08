# -*- coding: utf-8 -*-
"""
日志工具
- 统一日志格式
- 支持请求、异常、业务操作记录
"""
import logging
import sys

# 配置根 logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

logger = logging.getLogger('monitor')
