# -*- coding: utf-8 -*-
"""
统一 API 响应格式（工具类）
- success: 成功响应
- error: 失败响应
"""
from django.http import JsonResponse


def success(data=None, msg='success'):
    """成功响应"""
    return JsonResponse({
        'code': 200,
        'msg': msg,
        'data': data or {}
    })


def error(msg='error', code=400, status=200):
    """失败响应"""
    return JsonResponse({
        'code': code,
        'msg': msg,
        'data': {}
    }, status=status)
