# -*- coding: utf-8 -*-
from django.urls import path
from .views import (
    DeviceListView,
    DeviceSimpleListView,
    DeviceDetailView,
    DeviceBatchDeleteView
)

urlpatterns = [
    path('list/', DeviceListView.as_view(), name='device_list'),
    path('simple_list/', DeviceSimpleListView.as_view(), name='device_simple_list'),
    path('detail/', DeviceDetailView.as_view(), name='device_detail'),
    path('batch_delete/', DeviceBatchDeleteView.as_view(), name='device_batch_delete'),
]
