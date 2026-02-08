# -*- coding: utf-8 -*-
"""
初始化用户模拟数据
执行: python manage.py init_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.user.models import User


class Command(BaseCommand):
    help = '初始化用户模拟数据'

    def handle(self, *args, **options):
        users_data = [
            {
                'name': 'admin',
                'password': 'admin123',
                'type': 1,
                'device_list': [],
                'remark': '超级管理员，拥有全部权限'
            },
            {
                'name': 'zhangsan',
                'password': '123456',
                'type': 2,
                'device_list': ['device_001', 'device_002', 'device_003'],
                'remark': '客户，可查看设备001、002、003'
            },
            {
                'name': 'lisi',
                'password': '123456',
                'type': 2,
                'device_list': ['device_004', 'device_005'],
                'remark': '客户，可查看设备004、005'
            },
            {
                'name': 'wangwu',
                'password': '123456',
                'type': 2,
                'device_list': ['device_001', 'device_006'],
                'remark': '客户，可查看设备001、006'
            },
            {
                'name': 'zhaoliu',
                'password': '123456',
                'type': 2,
                'device_list': [],
                'remark': '客户，暂无分配设备'
            }
        ]

        created_count = 0
        for ud in users_data:
            if not User.objects.filter(name=ud['name'], is_delete=0).exists():
                User.objects.create(
                    name=ud['name'],
                    password=make_password(ud['password']),
                    type=ud['type'],
                    device_list=ud.get('device_list', [])
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'创建用户: {ud["name"]} ({ud["remark"]})'))

        self.stdout.write(self.style.SUCCESS(f'\n完成！共创建 {created_count} 个新用户。'))
        self.stdout.write('默认账号: admin / admin123 (超级管理员)')
        self.stdout.write('客户账号: zhangsan / 123456, lisi / 123456 等')
