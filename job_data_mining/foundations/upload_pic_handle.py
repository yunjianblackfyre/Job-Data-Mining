#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import struct
import py_decrypt_url
from common.http_handle import *
from conf.config import PIC_STORE

STORE_PIC_ERROR = -9001

class CUploadPicHttpHandle(CHttpHandle):
    
    #data = {'pic_id':'douban000010001s','data':'xxxx'}
    def __init__(self, data):
        self._url = 'http://%s:%s/%s'%(PIC_STORE['host'], PIC_STORE['port'], 'raw_overwritev2')
        self._data = data
        self._boundary = '------------------50ab45f06advb'
        super(CUploadPicHttpHandle, self).__init__(self._url)
        
    def get_module_name(self):
        return 'store_pic'
    
    def headers(self):
        header = {
                'Content-Type':'multipart/form-data; boundary=%s' % self._boundary
                }
        return header
    
    def req_encode(self):
        boundary = self._boundary
        data = []  
        data.append('--%s' % boundary)
        data.append('Content-Disposition: form-data; name="auth_appid"\r\n')
        data.append(PIC_STORE['auth_appid'])
        data.append('--%s' % boundary)
        data.append('Content-Disposition: form-data; name="fileid"\r\n')
        data.append(str(self._data['pic_id']))
        data.append('--%s' % boundary)
        '''data.append('Content-Disposition: form-data; name="uin"\r\n')
        data.append(str(self._data['movie_id']))
        data.append('--%s' % boundary)
        data.append('Content-Disposition: form-data; name="parentid"\r\n')
        data.append(PIC_STORE['parentid'])
        data.append('--%s' % boundary)'''
        data.append('Content-Disposition: form-data; name="deal_flag"\r\n')
        data.append('1')
        data.append('--%s' % boundary)
        data.append('Content-Disposition: form-data; name="data"; filename="pic.jpg"')
        data.append('Content-Type: image/jpeg\r\n')
        data.append(self._data['data'])
        data.append('--%s\r\n\r\n' % boundary)
        httpBody = '\r\n'.encode().join(self.tobyte(data))
        return httpBody
    
    def tobyte(self, li):
        dst = []
        for i in li:
            if isinstance(i, bytes):
                dst.append(i)
            elif isinstance(i, str):
                dst.append(i.encode())
            elif isinstance(i, int):
                dst.append(struct.pack(">H", i))
        return dst
    
    def rsp_decode(self, data):
        try:
            json_data = json.loads(data)
            if 'retcode' not in json_data:
                log_error('upload pic[%s] except no retcode' % self._data['pic_id'])
                return (STORE_PIC_ERROR, )
            if json_data['retcode'] != '0':
                log_error('upload pic[%s] error[%s]' % (self._data['pic_id'], json_data['retcode']))
                return (json_data['retcode'], )
            file_id = self._data['pic_id']
            enc_id = py_decrypt_url.func(0, PIC_STORE['urlKey'], file_id)
            return (0, PIC_STORE['urlRet']+enc_id)
        except Exception as e:
            log_error('decode json except:' + str(e))
            raise Exc(STORE_PIC_ERROR, str(e))

if __name__ == '__main__':
    #import base64
    log_init(log_path='./', log_name='uploadpic.log', log_level=4, log_mode='time')
    with open('view_photo_photo_public_p2364363557.jpg', 'rb') as f:
        #content = base64.b64encode(f.read())
        content = f.read()
    data = {'pic_id':'10001douban2643635571','data':content}
    op = CUploadPicHttpHandle(data)
    print(op.process())

