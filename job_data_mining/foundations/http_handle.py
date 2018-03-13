#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import urllib.error
from common.exception import Exc
from common.log import *

class CHttpHandle():
    
    def __init__(self, url, data={}, method='post'):
        self._httpMethod = method
        self._reqData = data
        self._httpUrl = url
        self._timeout = 600
        
    def get_module_name(self):
        return ''
        
    def headers(self):
        return {}
        
    def req_encode(self):
        return self._reqData

    def rsp_decode(self, data):
        return

    def process(self):
        req_head = self.headers()
        req_data = self.req_encode()
        if not isinstance(req_data, (str, bytes)):
            req_data = urllib.parse.urlencode(req_data)
        if self.get_module_name() != 'store_pic':
            log_debug('send %s to %s url:%s' % (req_data, self.get_module_name(), self._httpUrl))
        try:
            if self._httpMethod.upper() in ('GET',):
                req = urllib.request.Request('%s?%s' % (self._httpUrl, req_data), headers=req_head)
            else:
                if not isinstance(req_data, bytes):
                    req_data = req_data.encode()
                req = urllib.request.Request(self._httpUrl, req_data, req_head)
            rsp = urllib.request.urlopen(req, timeout=self._timeout)
            recv_data = rsp.read()
        except urllib.error.HTTPError as e:
            log_error(e)
            log_error(e.read())
            raise Exc(e.code, e.reason)
        except urllib.error.URLError as e:
            log_error(e)
            raise Exc(-1, e.reason)
        except Exception as e:
            log_error(e)
            raise Exc(-1, e)
        log_debug('%s recv %s' % (self.get_module_name(), recv_data.decode()))
        return self.rsp_decode(recv_data.decode())

