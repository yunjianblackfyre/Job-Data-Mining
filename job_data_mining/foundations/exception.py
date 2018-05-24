#   AUTHOR: Sibyl System
#     DATE: 2018-04-19
#     DESC: exception for all


ERROR_NOTIMPLEMENTED        = 1099


class Exc(Exception):
    def __init__(self, errcode, errinfo):
        Exception.__init__(self, errinfo)
        self._errcode = errcode
        self._errinfo = errinfo
        
    def get_errcode(self):
        return self._errcode
    
    def get_errinfo(self):
        return self._errinfo
    
    def __str__(self):
        info = 'exception: %d, %s' % (self._errcode, self._errinfo)
        return info
        

class NotImplementedException(Exc):
    def __init__(self, errcode=ERROR_NOTIMPLEMENTED, errinfo='not implemented'):
        Exc.__init__(self, errcode, errinfo)
