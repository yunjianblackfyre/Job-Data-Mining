#   AUTHOR: Sibyl System
#     DATE: 2017-12-30
#     DESC: sched

import logging
import os
import sys
import time

class CLog(object):
    '''
    日志类
    '''
    LEVEL_MAP = {
            0:logging.CRITICAL,
            1:logging.ERROR,
            2:logging.WARNING,
            3:logging.INFO,
            4:logging.DEBUG
            }

    @staticmethod
    def instance():
        global inst
        try:
            inst
        except Exception as e:
            inst = CLog()
        return inst
        
    @staticmethod
    def get_real_msg_by_frame(msg, f):
        return '[%s] [%s] [%s] <%s>' % (os.path.basename(f.f_code.co_filename), f.f_code.co_name,
            f.f_lineno, msg)
            
    @staticmethod
    def get_real_msg(msg):
        """ 根据调用关系取得日志产生所有文件名、函数名和行号，由此生成日志消息前缀 """
        f = sys._getframe().f_back.f_back.f_back
        if f is None: f = sys._getframe().f_back.f_back
        return CLog.get_real_msg_by_frame(msg, f)
        
    def __init__(self):
        self._proj = ''
        self._log_dir = None
        self._log_prefix = None
        self._log_level = 4
        self._last_log_name = None
        self._logger = None
        self._b_stream_init = False
        self._last_file_handle = None
        
    def init(self, proj, log_dir, log_prefix, log_level):
        self._proj = proj
        if log_dir[-1] != '/':
            self._log_dir = log_dir + '/'
        else:
            self._log_dir = log_dir
        self._log_prefix = log_prefix
        if log_level < 0:
            log_level = 0
        elif log_level > 4:
            log_level = 4
        self._log_level = log_level
        # 如果目录不存在创建目录
        if not os.access(self._log_dir, os.F_OK):
            try:
                os.makedirs(self._log_dir)
            except OSError as e:
                return -1
        return 0
    # 检查日志名，是否需要重新载入日志文件,为True说明不需要重新载入，False说明需要重新载入
    
    def check_log_name(self):
        # 没有初始化时也不需要重新载入
        if self._log_dir is None or self._log_prefix is None:
            return (True, None)
        log_name_arr = [self._log_dir, self._log_prefix, '_', time.strftime('%Y%m%d'), '.log']
        log_name = ''.join(log_name_arr)
        if self._last_log_name != log_name or not os.path.exists(log_name):
            return (False, log_name)
        else:
            return (True, log_name)
            
    def init_logger(self):
        self._logger = logging.getLogger(self._proj)
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(process)d] [%(thread)d] %(message)s')
        if not self._b_stream_init:
            stream_handler = logging.StreamHandler(sys.stderr)
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(logging.INFO)
            self._logger.addHandler(stream_handler)
            self._b_stream_init = True
        ret = self.check_log_name()
        if ret[0]:
            return 0
        try:
            log_file_handler = logging.FileHandler(ret[1], encoding='utf-8')
            log_file_handler.setFormatter(formatter)
            log_file_handler.setLevel(CLog.LEVEL_MAP[self._log_level])
            self._logger.addHandler(log_file_handler)
            if self._last_file_handle is not None:
                self._logger.removeHandler(self._last_file_handle)
                self._last_file_handle.close()
            self._last_file_handle = log_file_handler
            self._last_log_name = ret[1]
        except:
            pass
        return 0
        
    def log_debug(self, msg):
        self.init_logger()
        self._logger.debug(CLog.get_real_msg(msg))
        
    def log_info(self, msg):
        self.init_logger()
        self._logger.info(CLog.get_real_msg(msg))
        
    def log_warning(self, msg):
        self.init_logger()
        self._logger.warning(CLog.get_real_msg(msg))
        
    def log_error(self, msg):
        self.init_logger()
        self._logger.error(CLog.get_real_msg(msg))
        
    def log_critical(self, msg):
        self.init_logger()
        self._logger.critical(CLog.get_real_msg(msg))

# 创建一个全局日志
# 不在屏幕打印信息
def log_no_stderr():
    CLog.instance()._b_stream_init = True
    
def log_init(proj, log_dir, log_prefix, log_level=4):
    return CLog.instance().init(proj, log_dir, log_prefix, log_level)

def log_debug(msg):
    CLog.instance().log_debug(msg)
    
def log_info(msg):
    CLog.instance().log_info(msg)
    
def log_warning(msg):
    CLog.instance().log_warning(msg)
    
def log_error(msg):
    CLog.instance().log_error(msg)
    
def log_critical(msg):
    CLog.instance().log_critical(msg)
    
    

if __name__ == '__main__':
    log_init('test', './', 'test', 4)
    CLog.instance().log_info('xxxxxxxx')
    log_info('蚂蚁竞走十年了')

