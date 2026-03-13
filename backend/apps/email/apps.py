# -*- coding: utf-8 -*-
from django.apps import AppConfig


class EmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.email'
    verbose_name = '邮箱管理'
