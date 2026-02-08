from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from .models import User

class UserView(View):
    def get(self, request):
        return JsonResponse({'code': 200, 'msg': 'success'})
    def post(self, request):
        return JsonResponse({'code': 200, 'msg': 'success'})
    def put(self, request):
        return JsonResponse({'code': 200, 'msg': 'success'})
    def delete(self, request):
        return JsonResponse({'code': 200, 'msg': 'success'})