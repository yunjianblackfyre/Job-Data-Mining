#   AUTHOR: Sibyl System
#     DATE: 2018-01-03
#     DESC: db handler for preprocessor

from config.interfaces import DB_INTERFACE_CFG

from foundations.mysql_client import MysqlClient

class CSrchDbHandle(MysqlClient):
    
    def __init__(self):
        super(CSrchDbHandle, self).__init__(**DB_INTERFACE_CFG)

if __name__ == '__main__':
    f = CSrchDbHandle()
    f.destroy()
    print('活过，爱过，写作过')

