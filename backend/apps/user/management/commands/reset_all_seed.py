# -*- coding: utf-8 -*-
"""
重置并重新造数（test + jdhydevicedb）
执行:
  python manage.py reset_all_seed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import connections, transaction
from django.utils import timezone

from apps.user.models import User


class Command(BaseCommand):
    help = '清空并重建用户与原始业务数据（用于本地演示）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('开始重置数据...'))

        self._reset_users()
        self._reset_raw_tables()

        self.stdout.write(self.style.SUCCESS('\n重置完成。'))
        self.stdout.write(self.style.SUCCESS('管理员账号: admin'))
        self.stdout.write(self.style.SUCCESS('管理员密码: Admin@123456'))
        self.stdout.write(self.style.SUCCESS('测试用户: demo_user'))
        self.stdout.write(self.style.SUCCESS('测试密码: Demo@123456'))

    @transaction.atomic
    def _reset_users(self):
        User.objects.all().delete()

        User.objects.create(
            name='admin',
            password=make_password('Admin@123456'),
            type=1,
            device_list=[]
        )

        User.objects.create(
            name='demo_user',
            password=make_password('Demo@123456'),
            type=2,
            device_list=['NB001', 'NB002', 'AP001']
        )

        self.stdout.write(self.style.SUCCESS('test库用户数据已重建（2个用户）'))

    def _reset_raw_tables(self):
        # 不再改动原始库 jdhydevicedb，避免覆盖客户原始数据
        self.stdout.write(self.style.WARNING('已跳过原始库数据重建（保留客户原始数据不变）'))
