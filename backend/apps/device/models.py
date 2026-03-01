# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone


class DeviceInfo(models.Model):
    """设备基础信息表"""
    DEVICE_TYPE_CHOICES = [
        ('buoy', '浮标'),
        ('station', '气象站')
    ]

    device_id = models.CharField(max_length=64, unique=True, verbose_name='设备ID', help_text='设备ID')
    device_name = models.CharField(max_length=100, verbose_name='设备名称', help_text='设备名称')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='buoy', verbose_name='设备类型')
    area_name = models.CharField(max_length=50, default='亚太', verbose_name='区域名称')
    latitude = models.DecimalField(max_digits=12, decimal_places=7, null=True, blank=True, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=12, decimal_places=7, null=True, blank=True, verbose_name='经度')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    status = models.IntegerField(default=0, verbose_name='状态', help_text='0: 离线, 1: 在线')
    last_report_time = models.DateTimeField(null=True, blank=True, verbose_name='最后上报时间')
    is_delete = models.IntegerField(default=0, verbose_name='是否删除', help_text='0: 未删除, 1: 已删除')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '设备基础信息'
        verbose_name_plural = '设备基础信息'
        db_table = 't_device_info'
        ordering = ['-create_time']

    @property
    def is_online(self):
        """24小时内有上报视为在线"""
        if not self.last_report_time:
            return False
        return self.last_report_time >= timezone.now() - timezone.timedelta(hours=24)


class DeviceData(models.Model):
    """设备业务数据表（初始化版本，吸收客户原始字段中的核心数据）"""
    device = models.ForeignKey(DeviceInfo, on_delete=models.CASCADE, related_name='data_list', verbose_name='设备')
    sn = models.BigIntegerField(null=True, blank=True, verbose_name='包序号')
    packet_time = models.DateTimeField(verbose_name='数据时间')
    iridium_id = models.CharField(max_length=255, blank=True, default='', verbose_name='铱星编号')

    latitude = models.DecimalField(max_digits=12, decimal_places=7, null=True, blank=True, verbose_name='纬度')
    longitude = models.DecimalField(max_digits=12, decimal_places=7, null=True, blank=True, verbose_name='经度')

    board_voltage = models.FloatField(null=True, blank=True, verbose_name='板子电压')
    board_temp = models.FloatField(null=True, blank=True, verbose_name='板子温度')
    air_temp = models.FloatField(null=True, blank=True, verbose_name='空气温度')
    air_humid = models.FloatField(null=True, blank=True, verbose_name='空气湿度')
    atmosphere = models.FloatField(null=True, blank=True, verbose_name='大气压力')
    wind_speed = models.FloatField(null=True, blank=True, verbose_name='风速')
    wind_direct = models.FloatField(null=True, blank=True, verbose_name='风向')

    raw_payload = models.JSONField(default=dict, blank=True, verbose_name='原始扩展数据')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '设备业务数据'
        verbose_name_plural = '设备业务数据'
        db_table = 't_device_data'
        ordering = ['-packet_time', '-id']
