# -*- coding: utf-8 -*-
from django.db import models


class DeviceInfo(models.Model):
    """设备基础信息表"""
    device_id = models.CharField(max_length=64, unique=True, verbose_name='设备ID', help_text='设备ID')
    device_name = models.CharField(max_length=100, verbose_name='设备名称', help_text='设备名称')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    status = models.IntegerField(default=0, verbose_name='状态', help_text='0: 离线, 1: 在线')
    is_delete = models.IntegerField(default=0, verbose_name='是否删除', help_text='0: 未删除, 1: 已删除')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '设备基础信息'
        verbose_name_plural = '设备基础信息'
        db_table = 't_device_info'
        ordering = ['-create_time']
