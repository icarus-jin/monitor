# -*- coding: utf-8 -*-
from django.urls import path

from .views import EmailLoginView, EmailListView, EmailDetailView, EmailDownloadView, EmailDeleteDownloadedView, EmailDownloadPackageView

urlpatterns = [
    path('login/', EmailLoginView.as_view(), name='email_login'),
    path('list/', EmailListView.as_view(), name='email_list'),
    path('detail/', EmailDetailView.as_view(), name='email_detail'),
    path('download/', EmailDownloadView.as_view(), name='email_download'),
    path('download_package/', EmailDownloadPackageView.as_view(), name='email_download_package'),
    path('delete_downloaded/', EmailDeleteDownloadedView.as_view(), name='email_delete_downloaded')
]
