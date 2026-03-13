# -*- coding: utf-8 -*-
import os
import sys

import django


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_server.settings')
    django.setup()

    from .server import run_server

    run_server(host='0.0.0.0', port=8088)


if __name__ == '__main__':
    main()
