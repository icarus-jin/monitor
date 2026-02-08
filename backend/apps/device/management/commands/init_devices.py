# -*- coding: utf-8 -*-
"""
初始化设备模拟数据
执行: python manage.py init_devices
"""
from django.core.management.base import BaseCommand
from apps.device.models import DeviceInfo


class Command(BaseCommand):
    help = '初始化设备模拟数据'

    def handle(self, *args, **options):
        devices = [
            {'device_id': 'device_001', 'device_name': '南极浮标A', 'remark': '南极区域浮标'},
            {'device_id': 'device_002', 'device_name': '南极浮标B', 'remark': '南极区域浮标'},
            {'device_id': 'device_003', 'device_name': '南极浮标C', 'remark': '南极区域浮标'},
            {'device_id': 'device_004', 'device_name': '北极气象站A', 'remark': '北极区域气象站'},
            {'device_id': 'device_005', 'device_name': '北极气象站B', 'remark': '北极区域气象站'},
            {'device_id': 'device_006', 'device_name': '亚太气象站A', 'remark': '亚太区域气象站'},
        ]
        created = 0
        for d in devices:
            if not DeviceInfo.objects.filter(device_id=d['device_id'], is_delete=0).exists():
                DeviceInfo.objects.create(**d)
                created += 1
                self.stdout.write(self.style.SUCCESS(f"创建设备: {d['device_name']} ({d['device_id']})"))
        self.stdout.write(self.style.SUCCESS(f'\n完成！共创建 {created} 个设备。'))
