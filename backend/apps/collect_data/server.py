# -*- coding: utf-8 -*-
import socketserver
from datetime import datetime

from utils.log import logger, request_logger

from .receive_log import insert_receive_log, build_stage_status
from .data_save import get_device_by_iridiumid, parse_payload_by_sensorflag
from .utils import bytes_to_iridiumid

from .checks import check_data, bytes_to_hex


def _log_partial_request(client_ip: str, raw_bytes: bytes):
    try:
        receive_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        request_hex = bytes_to_hex(raw_bytes)
        result_text = 'invalid packet'
        result_status = build_stage_status(result_text, is_valid_packet=False)

        iridiumid = ''
        sensorflag = ''
        devid = ''
        try:
            if len(raw_bytes) >= 25:
                iridiumid = bytes_to_iridiumid(raw_bytes[10:25])
        except Exception:
            iridiumid = ''

        if iridiumid:
            device = get_device_by_iridiumid(iridiumid)
            if device:
                sensorflag = str(device.get('sensorflag') or '')
                devid = device.get('devid') or ''

        insert_receive_log(
            ip=client_ip,
            request_time=receive_time,
            iridiumid=iridiumid,
            sensorflag=sensorflag,
            device_id=devid,
            sn=0,
            packet_len=len(raw_bytes),
            result_status=result_status,
            message=result_text,
            raw_hex=request_hex,
            parse_result=result_text,
        )

        request_logger.info(
            'ip=%s time=%s data=%s result=%s',
            client_ip,
            receive_time,
            request_hex,
            result_text
        )
    except Exception as exc:
        logger.exception('记录短包失败: %s', exc)


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logger.info('客户端已连接')
        buffer = bytearray()
        logged_partial = False
        try:
            while True:
                chunk = self.request.recv(4096)
                if not chunk:
                    break
                buffer.extend(chunk)
                processed_any = False

                while True:
                    if len(buffer) < 3:
                        break
                    if buffer[0] != 0x01:
                        try:
                            next_start = buffer.index(0x01)
                        except ValueError:
                            if buffer and not logged_partial:
                                _log_partial_request(self.client_address[0], bytes(buffer))
                                logged_partial = True
                            buffer.clear()
                            break
                        if next_start > 0 and not logged_partial:
                            _log_partial_request(self.client_address[0], bytes(buffer[:next_start]))
                            logged_partial = True
                        del buffer[:next_start]
                        if len(buffer) < 3:
                            break

                    rlen = int.from_bytes(buffer[1:3], byteorder="big", signed=False)
                    total_len = rlen + 3
                    if len(buffer) < total_len:
                        if not processed_any and buffer and not logged_partial:
                            _log_partial_request(self.client_address[0], bytes(buffer))
                            logged_partial = True
                        break

                    packet = bytes(buffer[:total_len])
                    del buffer[:total_len]
                    processed_any = True

                    receive_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    request_hex = bytes_to_hex(packet)
                    logger.info('Receive: %s', request_hex)
                    parse_payload = ''
                    parse_error = ''
                    sn_value = 0
                    iridiumid = ''
                    sensorflag = ''
                    devid = ''
                    try:
                        iridiumid = bytes_to_iridiumid(packet[10:25])
                    except Exception:
                        iridiumid = ''

                    if iridiumid:
                        device = get_device_by_iridiumid(iridiumid)
                        if device:
                            sensorflag = str(device.get('sensorflag') or '')
                            devid = device.get('devid') or ''

                    try:
                        if sensorflag:
                            parse_payload = parse_payload_by_sensorflag(sensorflag, packet)
                            try:
                                sn_value = int(parse_payload.get('sn') or 0)
                            except Exception:
                                sn_value = 0
                    except Exception as exc:
                        parse_error = str(exc)
                        parse_payload = ''

                    if check_data(packet):
                        from .data_save import data_save

                        result = data_save(packet)
                        logger.info(result.reply)
                        if not sn_value:
                            try:
                                sn_value = int.from_bytes(packet[25:28], byteorder='big')
                            except Exception:
                                sn_value = 0
                    else:
                        result = None
                        logger.info('error data: %s', request_hex)

                    if not parse_payload:
                        try:
                            parsed = {
                                'iridiumid': bytes_to_iridiumid(packet[10:25]),
                                'sn': int.from_bytes(packet[25:28], byteorder='big'),
                            }
                            parse_payload = parsed
                        except Exception as exc:
                            parse_error = str(exc)

                    result_text = result.reply if result else 'invalid packet'
                    result_status = build_stage_status(result_text, is_valid_packet=bool(result))
                    if result is None and not parse_error:
                        parse_error = result_text

                    parse_result_text = ''
                    if isinstance(parse_payload, dict):
                        try:
                            import json
                            parse_result_text = json.dumps(parse_payload, ensure_ascii=False)
                        except Exception:
                            parse_result_text = str(parse_payload)
                    else:
                        parse_result_text = str(parse_payload or '')
                    if not parse_result_text:
                        parse_result_text = str(parse_error or '')

                    insert_receive_log(
                        ip=self.client_address[0],
                        request_time=receive_time,
                        iridiumid=iridiumid,
                        sensorflag=sensorflag,
                        device_id=devid,
                        sn=sn_value,
                        packet_len=len(packet),
                        result_status=result_status,
                        message=result_text,
                        raw_hex=request_hex,
                        parse_result=parse_result_text,
                    )

                    request_logger.info(
                        'ip=%s time=%s data=%s result=%s',
                        self.client_address[0],
                        receive_time,
                        request_hex,
                        result_text
                    )

                if not processed_any and buffer and not logged_partial:
                    _log_partial_request(self.client_address[0], bytes(buffer))
                    logged_partial = True
        finally:
            if buffer and not logged_partial:
                _log_partial_request(self.client_address[0], bytes(buffer))
            logger.info('客户端已断开')


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def run_server(host='0.0.0.0', port=8088):
    with ThreadedTCPServer((host, port), TCPHandler) as server:
        logger.info('服务器已启动')
        logger.info('the port of server is %s', port)
        logger.info('the address of server is %s', host)
        server.serve_forever()
