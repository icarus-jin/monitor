# -*- coding: utf-8 -*-
"""
JSON 及请求体解析工具
- parse_body: 解析请求体（支持 JSON / form-urlencoded）
- get_param: 从 body 中获取参数（兼容 list 值取首项）
"""
import json
from urllib.parse import parse_qs


def parse_body(request):
    """
    解析请求体：支持 JSON 和 form-urlencoded
    - application/json -> dict
    - application/x-www-form-urlencoded -> dict (POST 自动解析，PUT 手动解析)
    """
    content_type = request.content_type or ''
    if 'application/json' in content_type:
        try:
            return json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return {}
    if request.method == 'POST' and request.POST:
        return {k: v for k, v in request.POST.lists()}
    if request.method == 'PUT' and request.body:
        try:
            parsed = parse_qs(request.body.decode('utf-8'))
            return {k: v for k, v in parsed.items()}
        except Exception:
            pass
    if request.method == 'GET' and request.GET:
        return {k: v for k, v in request.GET.lists()}
    return {}


def get_param(body_or_post, key, default=None):
    """
    从 body 中获取参数
    - POST form-urlencoded 的值为 list 时取第一个
    - JSON body 直接返回值
    """
    v = body_or_post.get(key, default)
    if isinstance(v, list) and v:
        return v[0]
    return v
