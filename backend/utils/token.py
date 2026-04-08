# -*- coding: utf-8 -*-
"""
Token 工具
- 存储、验证、删除 token
- 开发环境使用内存存储，生产环境建议使用 Redis
"""
import uuid


class TokenStore:
    """Token 存储（开发用，生产环境建议使用 Redis）"""
    _store = {}

    @classmethod
    def generate(cls):
        """生成新 token"""
        return str(uuid.uuid4())

    @classmethod
    def set(cls, token, user_id, username, expire_hours=24):
        """存储 token"""
        cls._store[token] = {
            'user_id': user_id,
            'username': username,
        }

    @classmethod
    def get(cls, token):
        """获取 token 对应的用户信息"""
        if not token:
            return None
        return cls._store.get(token)

    @classmethod
    def remove(cls, token):
        """删除 token"""
        if token in cls._store:
            del cls._store[token]


token_store = TokenStore()
