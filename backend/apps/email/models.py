# -*- coding: utf-8 -*-
from django.db import models


class EmailAccount(models.Model):
    user_id = models.IntegerField(db_index=True)
    email = models.CharField(max_length=255, db_index=True)
    imap_host = models.CharField(max_length=120, default='imap.163.com')
    imap_port = models.IntegerField(default=993)
    auth_code = models.CharField(max_length=512)
    is_active = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_account'
        verbose_name = '邮箱账号'
        verbose_name_plural = '邮箱账号'


class EmailTaskLog(models.Model):
    user_id = models.IntegerField(db_index=True)
    email = models.CharField(max_length=255, db_index=True)
    action = models.CharField(max_length=50)
    request_params = models.TextField(default='')
    result = models.TextField(default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_task_log'
        verbose_name = '邮箱任务日志'
        verbose_name_plural = '邮箱任务日志'


class EmailAttachmentLog(models.Model):
    user_id = models.IntegerField(db_index=True)
    email = models.CharField(max_length=255, db_index=True)
    email_id = models.CharField(max_length=128, db_index=True)
    subject = models.TextField(default='')
    folder_name = models.CharField(max_length=128, default='')
    file_name = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=20, default='success')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_attachment_log'
        verbose_name = '邮箱附件日志'
        verbose_name_plural = '邮箱附件日志'
