from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100, verbose_name='用户名', help_text='用户名')
    password = models.CharField(max_length=100, verbose_name='密码', help_text='密码')
    type = models.IntegerField(choices=[(1, '超级管理员'), (2, '客户')], default=1, verbose_name='用户类型')
    device_list = models.JSONField(default=list, verbose_name='设备列表', help_text='设备列表')
    is_delete = models.IntegerField(default=0, verbose_name='是否删除', help_text='0: 未删除, 1: 已删除')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间', help_text='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间', help_text='更新时间')

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'
        db_table = 't_user'
        ordering = ['-create_time']