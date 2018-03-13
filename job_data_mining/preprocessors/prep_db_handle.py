#!/usr/bin/python
# -*- coding: utf-8 -*-

from config.interfaces import DB_INTERFACE_CFG

from foundations.mysql_client import MysqlClient

class CPrepDbHandle(MysqlClient):
    
    def __init__(self):
        super(CPrepDbHandle, self).__init__(**DB_INTERFACE_CFG)

if __name__ == '__main__':
    f = CPrepDbHandle()
    f.destroy()
    print('What a fine day')

