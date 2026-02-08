# -*- coding: utf-8 -*-
"""
设备基础信息视图
"""
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from .models import DeviceInfo
from utils import success, error, parse_body, get_param, logger


@method_decorator(csrf_exempt, name='dispatch')
class DeviceListView(View):
    """设备列表（分页、搜索）"""
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            name = (request.GET.get('name') or '').strip()
            device_id = (request.GET.get('device_id') or '').strip()
            qs = DeviceInfo.objects.filter(is_delete=0).order_by('-create_time')
            if name:
                qs = qs.filter(device_name__icontains=name)
            if device_id:
                qs = qs.filter(device_id__icontains=device_id)
            total = qs.count()
            paginator = Paginator(qs, page_size)
            page_obj = paginator.get_page(page)
            device_list = [
                {
                    'id': d.id,
                    'device_id': d.device_id,
                    'device_name': d.device_name,
                    'remark': d.remark or '',
                    'status': d.status,
                    'status_name': '在线' if d.status == 1 else '离线',
                    'create_time': d.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'update_time': d.update_time.strftime('%Y-%m-%d %H:%M:%S')
                }
                for d in page_obj
            ]
            return success(data={'device_list': device_list, 'total': total})
        except Exception as e:
            logger.exception('设备列表异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceSimpleListView(View):
    """设备简要列表（用于下拉、多选等，不分页）"""
    def get(self, request):
        try:
            qs = DeviceInfo.objects.filter(is_delete=0).order_by('device_id')
            device_list = [
                {'id': d.id, 'device_id': d.device_id, 'device_name': d.device_name}
                for d in qs
            ]
            return success(data={'device_list': device_list})
        except Exception as e:
            logger.exception('设备简要列表异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceDetailView(View):
    """设备增删改"""
    def post(self, request):
        """新增设备"""
        try:
            body = parse_body(request)
            device_id = (get_param(body, 'device_id') or '').strip()
            device_name = (get_param(body, 'device_name') or '').strip()
            remark = (get_param(body, 'remark') or '').strip()
            if not device_id:
                return error('设备ID不能为空', code=400)
            if not device_name:
                return error('设备名称不能为空', code=400)
            if DeviceInfo.objects.filter(device_id=device_id, is_delete=0).exists():
                return error('设备ID已存在', code=400)
            DeviceInfo.objects.create(
                device_id=device_id,
                device_name=device_name,
                remark=remark
            )
            logger.info('新增设备: %s (%s)', device_name, device_id)
            return success(msg='新增成功')
        except Exception as e:
            logger.exception('新增设备异常: %s', e)
            return error(str(e), code=500)

    def put(self, request):
        """编辑设备"""
        try:
            body = parse_body(request)
            uid = get_param(body, 'id') or body.get('id')
            if not uid:
                return error('设备ID不能为空', code=400)
            device = DeviceInfo.objects.filter(id=uid, is_delete=0).first()
            if not device:
                return error('设备不存在', code=404)
            device_name = get_param(body, 'device_name')
            if device_name is not None:
                device.device_name = device_name.strip()
            remark = get_param(body, 'remark')
            if remark is not None:
                device.remark = remark.strip()
            status = get_param(body, 'status')
            if status is not None and status != '':
                device.status = int(status)
            device.save()
            logger.info('编辑设备: id=%s', device.id)
            return success(msg='编辑成功')
        except Exception as e:
            logger.exception('编辑设备异常: %s', e)
            return error(str(e), code=500)

    def delete(self, request):
        """删除设备（软删除）"""
        try:
            uid = request.GET.get('id') or get_param(parse_body(request), 'id')
            if not uid:
                return error('设备ID不能为空', code=400)
            device = DeviceInfo.objects.filter(id=uid, is_delete=0).first()
            if not device:
                return error('设备不存在', code=404)
            device.is_delete = 1
            device.save()
            logger.info('删除设备: %s (id=%s)', device.device_name, device.id)
            return success(msg='删除成功')
        except Exception as e:
            logger.exception('删除设备异常: %s', e)
            return error(str(e), code=500)


@method_decorator(csrf_exempt, name='dispatch')
class DeviceBatchDeleteView(View):
    """批量删除设备"""
    def post(self, request):
        try:
            body = parse_body(request)
            ids = body.get('ids') or body.get('id_list') or []
            if isinstance(ids, str):
                ids = [x.strip() for x in ids.split(',') if x.strip()]
            if not ids:
                return error('请选择要删除的设备', code=400)
            DeviceInfo.objects.filter(id__in=ids, is_delete=0).update(is_delete=1)
            logger.info('批量删除设备: ids=%s', ids)
            return success(msg='批量删除成功')
        except Exception as e:
            logger.exception('批量删除异常: %s', e)
            return error(str(e), code=500)
