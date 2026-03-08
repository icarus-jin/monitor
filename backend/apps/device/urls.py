# -*- coding: utf-8 -*-
from django.urls import path
from .views import (
    DeviceListView,
    DeviceSimpleListView,
    DeviceMapPointsView,
    DeviceDetailView,
    DeviceBatchDeleteView,
    DeviceDataIngestView,
    DeviceDataLatestView,
    DeviceTrendView,
    DeviceTrackView,
    DeviceOverviewView,
    DeviceExportView,
    MapTileProxyView,
)

urlpatterns = [
    path('list/', DeviceListView.as_view(), name='device_list'),
    path('simple_list/', DeviceSimpleListView.as_view(), name='device_simple_list'),
    path('map/points/', DeviceMapPointsView.as_view(), name='device_map_points'),
    path('detail/', DeviceDetailView.as_view(), name='device_detail'),
    path('batch_delete/', DeviceBatchDeleteView.as_view(), name='device_batch_delete'),

    path('data/ingest/', DeviceDataIngestView.as_view(), name='device_data_ingest'),
    path('data/latest/', DeviceDataLatestView.as_view(), name='device_data_latest'),
    path('data/trend/', DeviceTrendView.as_view(), name='device_data_trend'),
    path('track/', DeviceTrackView.as_view(), name='device_track'),
    path('overview/', DeviceOverviewView.as_view(), name='device_overview'),
    path('export/', DeviceExportView.as_view(), name='device_export'),
    path('map/tile/', MapTileProxyView.as_view(), name='map_tile_proxy'),
]
