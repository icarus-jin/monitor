# -*- coding: utf-8 -*-
from django.urls import path
from .views import (
    LoginView,
    UserListView,
    UserDetailView,
    UserBatchDeleteView,
    ResetPasswordView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('user_list/', UserListView.as_view(), name='user_list'),
    path('register/', UserDetailView.as_view(), name='user_register'),
    path('batch_delete/', UserBatchDeleteView.as_view(), name='user_batch_delete'),
    path('reset_password/', ResetPasswordView.as_view(), name='reset_password'),
]
