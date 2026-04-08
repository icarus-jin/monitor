# -*- coding: utf-8 -*-
from django.urls import path
from .views import ReceiveLogListView, ReceiveLogSendTCPView

urlpatterns = [
    path('list/', ReceiveLogListView.as_view(), name='receive_log_list'),
    path('send_tcp/', ReceiveLogSendTCPView.as_view(), name='receive_log_send_tcp'),
]
