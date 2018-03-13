#COPYRIGHT: Tencent flim
#   AUTHOR: paveehan
#     DATE: 2016-07-18
#     DESC: log

import os
import sys
import logging
import logging.handlers

from common.singleton import Singleton

LEVEL_MAP = {
    0:logging.CRITICAL,
    1:logging.ERROR,
    2:logging.WARNING,
    3:logging.INFO,
    4:logging.DEBUG
}

@Singleton
class CLog(object):

    def init(self, log_path, log_size, log_num, log_level, log_mode='size'):
        self._log_path = log_path
        self._log_size = log_size
        self._log_num = log_num
        self._log_level = log_level
        self._log_mode = log_mode
        self._init_logger()

    def _init_logger(self):
        self._logger = logging.getLogger()
        self._logger.setLevel(self._log_level)
        if self._log_mode == 'size':
            log_handler = logging.handlers.RotatingFileHandler(
                            filename='%s' % (self._log_path),
                            mode='a',
                            maxBytes=1024 * 1024 * self._log_size,
                            backupCount=self._log_num,
                            encoding='utf-8',
                            delay=0)
        elif self._log_mode == 'time':
            log_handler = logging.handlers.TimedRotatingFileHandler(
                            filename='%s' % (self._log_path),
                            when='D',
                            interval =1,
                            backupCount=self._log_num,
                            encoding='utf-8')

        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(process)d][%(thread)d]%(message)s')
        log_handler.setFormatter(formatter)

        self._logger.addHandler(log_handler)


    def log_debug(self, msg):
        self._logger.debug(self.get_real_msg(msg))

    def log_info(self, msg):
        self._logger.info(self.get_real_msg(msg))

    def log_warning(self, msg):
        self._logger.warning(self.get_real_msg(msg))

    def log_error(self, msg):
        self._logger.error(self.get_real_msg(msg))

    def log_critical(self, msg):
        self._logger.critical(self.get_real_msg(msg))

    def get_real_msg(self, msg):
        """根据调用关系取得日志产生所有文件名、函数名和行号，由此生成日志消息前缀
        """
        f = sys._getframe().f_back.f_back.f_back
        if f is None:
            f = sys._getframe().f_back.f_back

        return '[%s:%s] %s' % (os.path.basename(f.f_code.co_filename), f.f_lineno, msg)


def log_init(log_path, log_name, log_size=10, log_num=100, log_level=3, log_mode='size'):
    if not os.access(log_path, os.F_OK):
        os.makedirs(log_path)
    return CLog.instance().init(log_path+log_name, log_size, log_num, LEVEL_MAP[log_level], log_mode)

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
    log_init(log_path='./test/', log_name='test.log', log_level=4, log_mode='time')
    log_error('1111')
    log_debug('哈哈哈哈')

