# -*- coding: utf-8 -*-
from django.db import models


class ReceiveLog(models.Model):
    RESULT_CHOICES = [
        ('recv_failed', '接收失败'),
        ('parse_failed', '解析失败'),
        ('db_failed', '入库失败'),
        ('completed', '处理完成'),
    ]
    INGEST_STATUS_CHOICES = [
        ('ingested', '入库'),
        ('not_ingested', '未入库'),
    ]

    ip = models.CharField(max_length=64, default='', verbose_name='来源IP')
    time = models.DateTimeField(null=True, blank=True, verbose_name='请求时间')
    device_id = models.CharField(max_length=64, default='', verbose_name='设备ID')
    iridiumid = models.CharField(max_length=64, default='', verbose_name='铱星号')
    sensorflag = models.CharField(max_length=32, default='', verbose_name='传感器标志位')
    sn = models.IntegerField(default=0, verbose_name='序列号')
    packet_len = models.IntegerField(default=0, verbose_name='包长')
    result = models.CharField(max_length=16, choices=RESULT_CHOICES, default='failed', verbose_name='处理阶段')
    message = models.CharField(max_length=255, default='', verbose_name='处理说明')
    raw = models.TextField(blank=True, default='', verbose_name='原始内容')
    parse_result = models.TextField(blank=True, default='', verbose_name='解析结果')
    ingest_status = models.CharField(max_length=16, choices=INGEST_STATUS_CHOICES, default='not_ingested', verbose_name='入库状态')
    db_time = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    class Meta:
        verbose_name = '数据接收记录'
        verbose_name_plural = '数据接收记录'
        db_table = 't_receive_log'
        ordering = ['-id']
