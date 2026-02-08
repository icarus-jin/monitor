from django.urls import path,include
from .views import UserView

urlpatterns = [
    path('login/', UserView.as_view(), name='login'),
]
