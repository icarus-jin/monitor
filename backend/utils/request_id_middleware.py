# -*- coding: utf-8 -*-
from utils.log import new_request_id, set_request_id, clear_request_id


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.META.get('HTTP_X_REQUEST_ID') or new_request_id()
        set_request_id(rid)
        request.request_id = rid
        try:
            response = self.get_response(request)
            response['X-Request-Id'] = rid
            return response
        finally:
            clear_request_id()
