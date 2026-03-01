# -*- coding: utf-8 -*-
"""
用户管理视图
- 登录、登出
- 用户列表（分页、搜索）
- 新增、编辑、删除、批量删除
- 重置密码
"""
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator

from .models import User
from utils import token_store, success, error, parse_body, get_param, logger


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """登录"""
    def post(self, request):
        try:
            body = parse_body(request)
            name = get_param(body, 'username') or get_param(body, 'name')
            password = get_param(body, 'password')
            if not name or not password:
                return error('用户名和密码不能为空', code=400)
            user = User.objects.filter(name=name, is_delete=0).first()
            if not user:
                return error('用户名或密码错误', code=400)
            if not check_password(password, user.password):
                return error('用户名或密码错误', code=400)
            token = token_store.generate()
            token_store.set(token, user.id, user.name)
            request.session['user_id'] = user.id
            request.session['username'] = user.name
            request.session['token'] = token
            request.session.set_expiry(60 * 60 * 24)
            logger.info('用户登录: %s', user.name)
            return success(
                data={'token': token, 'username': user.name, 'user_type': user.type},
                msg='登录成功'
            )
        except Exception as e:
            logger.exception('登录异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserListView(View):
    """用户列表（分页、搜索）"""
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            name = (request.GET.get('name') or '').strip()
            qs = User.objects.filter(is_delete=0).order_by('id')
            if name:
                qs = qs.filter(name__icontains=name)
            total = qs.count()
            paginator = Paginator(qs, page_size)
            page_obj = paginator.get_page(page)
            user_list = [
                {
                    'id': u.id,
                    'name': u.name,
                    'type': u.type,
                    'type_name': '超级管理员' if u.type == 1 else '客户',
                    'device_list': u.device_list or [],
                    'device_list_str': ','.join(map(str, u.device_list or [])),
                    'create_time': u.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'update_time': u.update_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                for u in page_obj
            ]
            return success(data={'user_list': user_list, 'total': total})
        except Exception as e:
            logger.exception('用户列表异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserDetailView(View):
    """用户增删改"""
    def post(self, request):
        """新增用户"""
        try:
            body = parse_body(request)
            name = (get_param(body, 'name') or '').strip()
            password = get_param(body, 'password') or get_param(body, 'pwd')
            user_type = int(get_param(body, 'type') or 2)
            device_list = body.get('device_list')
            if isinstance(device_list, str):
                device_list = [x.strip() for x in device_list.split(',') if x.strip()]
            elif isinstance(device_list, list):
                device_list = [str(x).strip() for x in device_list if str(x).strip()]
            else:
                device_list = []
            if not name:
                return error('用户名不能为空', code=400)
            if not password or len(password) < 6:
                return error('密码不能少于6位', code=400)
            if User.objects.filter(name=name, is_delete=0).exists():
                return error('用户名已存在', code=400)
            User.objects.create(
                name=name,
                password=make_password(password),
                type=user_type,
                device_list=device_list
            )
            logger.info('新增用户: %s', name)
            return success(msg='新增成功')
        except Exception as e:
            logger.exception('新增用户异常: %s', e)
            return error(str(e), code=500)

    def put(self, request):
        """编辑用户"""
        try:
            body = parse_body(request)
            uid = get_param(body, 'id') or body.get('id')
            if not uid:
                return error('用户ID不能为空', code=400)
            user = User.objects.filter(id=uid, is_delete=0).first()
            if not user:
                return error('用户不存在', code=404)
            user_type = get_param(body, 'type') or body.get('type')
            if user_type is not None and user_type != '':
                user.type = int(user_type)
            device_list = body.get('device_list')
            if device_list is not None:
                if isinstance(device_list, str):
                    user.device_list = [x.strip() for x in device_list.split(',') if x.strip()]
                elif isinstance(device_list, list):
                    user.device_list = [str(x).strip() for x in device_list if str(x).strip()]
            user.save()
            logger.info('编辑用户: %s (id=%s)', user.name, user.id)
            return success(msg='编辑成功')
        except Exception as e:
            logger.exception('编辑用户异常: %s', e)
            return error(str(e), code=500)

    def delete(self, request):
        """删除用户（软删除）"""
        try:
            uid = request.GET.get('id') or get_param(parse_body(request), 'id') or request.POST.get('id')
            if not uid:
                return error('用户ID不能为空', code=400)
            user = User.objects.filter(id=uid, is_delete=0).first()
            if not user:
                return error('用户不存在', code=404)
            user.is_delete = 1
            user.save()
            logger.info('删除用户: %s (id=%s)', user.name, user.id)
            return success(msg='删除成功')
        except Exception as e:
            logger.exception('删除用户异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserBatchDeleteView(View):
    """批量删除用户"""
    def post(self, request):
        try:
            body = parse_body(request)
            ids = body.get('ids') or body.get('id_list') or []
            if isinstance(ids, str):
                ids = [x.strip() for x in ids.split(',') if x.strip()]
            if not ids:
                return error('请选择要删除的用户', code=400)
            User.objects.filter(id__in=ids, is_delete=0).update(is_delete=1)
            logger.info('批量删除用户: ids=%s', ids)
            return success(msg='批量删除成功')
        except Exception as e:
            logger.exception('批量删除异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(View):
    """重置密码"""
    def put(self, request):
        try:
            body = parse_body(request)
            uid = get_param(body, 'id') or body.get('id')
            new_pwd = get_param(body, 'new_pwd') or get_param(body, 'new_password')
            if not uid:
                return error('用户ID不能为空', code=400)
            if not new_pwd or len(new_pwd) < 6:
                return error('新密码不能少于6位', code=400)
            user = User.objects.filter(id=uid, is_delete=0).first()
            if not user:
                return error('用户不存在', code=404)
            user.password = make_password(new_pwd)
            user.save()
            logger.info('重置密码: 用户 id=%s', user.id)
            return success(msg='重置密码成功')
        except Exception as e:
            logger.exception('重置密码异常: %s', e)
            return error(str(e), code=500)

    def get(self, request):
        """兼容前端 GET 方式调用"""
        return self.put(request)
