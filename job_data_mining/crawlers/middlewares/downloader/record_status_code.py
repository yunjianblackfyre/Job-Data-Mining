import socket
import fcntl
import struct
import hashlib
from scrapy import signals
# from scrapy.xlib.pydispatch import dispatcher
from pydispatch import dispatcher
from common.log import *
from iqiyi_project.iqiyi_db_handle import CIqiyiDbHandle
from tools.network_tool import Ip_tool

logger = logging.getLogger(__name__)
# 任务状态码
TASK_STATE = {
    'init': 1,
    'downloading': 2,
    'failure': 3,
    'down_succ': 4,
    'exception': 5,
    'fetch_fail': 6,
    'fetch_succ': 7,
    'mix_succ': 8
}

class RecordStatusCodeMiddleware(object):
    """This middleware enables working with sites that change the user-agent"""

    def __init__(self, debug=False):
        self.task_db = CIqiyiDbHandle()
        self.task_stat_db = CIqiyiDbHandle()
        self.task_db.set_db_table('ysfans_iqiyi', 't_task')
        self.task_stat_db.set_db_table('ysfans_iqiyi', 't_task_stat')
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self):
        self.task_db.destroy()
        self.task_stat_db.destroy()

    def process_response(self, request, response, spider):
        status_code = response.status
        print('FFFFFFFF')
        print(status_code)
        task_id = request.meta.get('task_id')
        is_detail = request.meta.get('is_detail')
        log_debug("RESPONSE_PAGE:%s, status:%s, task_id:%s, time:%s" % (response.url, response.status, task_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        try:
            # 记录统计状态码信息
            self.record_status(status_code)
            # 非正常返回视为任务失败
            if is_detail:
                self.update_task_state(task_id)
        except Exception as e:
            log_error("MIDDLEWARE PROCESS RESPONSE:%s" % e)

        # 请求页面存储
        path = "/data/home/user00/data_html/iqiyi_data"
        if not os.path.exists(path):
            os.makedirs(path)
        # url_info = list(urllib.parse.urlparse(response.url))
        # url_path = url_info[2]
        # url_path = url_path.replace('/', '_').replace('.html', '')
        # url_params = urllib.parse.parse_qsl(url_info[4])
        # url_params = "_".join((dict(url_params).values())).replace('/', '_')
        # # 返回状态+url路径+url参数值
        # name = "%s_%s_%s.html" % (response.status, url_path, url_params)
        #write_time= time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())
        #md5_url = self.str2md5("%s_%s" % (write_time, response.url))
        md5_url = self.str2md5("%s" % (response.url))
        # 文件名为时间和url的md5值+返回状态+后缀.html
        prefixs = md5_url[0:3]
        suffixs = md5_url[-3:]
        path1 = "%s/%s" % (path,prefixs)
        if not os.path.exists(path1):
            os.makedirs(path1)
        path2 = "%s/%s" % (path1,suffixs)
        if not os.path.exists(path2):
            os.makedirs(path2)
        filename = "%s/%s_%s.html" % (path2, md5_url, response.status)
        log_debug("RESPONSE_PAGE:%s, status:%s, task_id:%s, filename:%s, md5_url:%s" % (response.url, response.status, task_id, filename, md5_url))
        with open(filename, 'wb') as file:
            file.write(response.body)
        return response

    def process_exception(self, request, exception, spider):
        # 超时或其他无response的状态码
        status = 1000
        task_id = request.meta.get('task_id')
        is_detail = request.meta.get('is_detail')
        log_error("RESPONSE_ERROR:%s exception:%s, task_id:%s, time:%s" % (request.url, exception, task_id, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        try:
            # 记录统计超时或其他失败信息
            self.record_status(status)
            # 详情页超时则将视为任务失败
            if is_detail:
                self.update_task_state(task_id)
        except Exception as e:
            log_error("MIDDLEWARE PROCESS EXCEPTION:%s" % e)

    # 更新任务状态(处理超时和错误情况)
    def update_task_state(self, task_id, state=TASK_STATE.get('failure')):
        task_detail = {
            'Ftask_state': state,
            'Fmodify_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        where = "Ftask_id='%s'" % (task_id)
        self.task_db.update(task_detail, where)
        self.task_db.commit()


    # 记录统计状态码信息
    def record_status(self, status_code):
        # ip = socket.gethostbyname(socket.gethostname())
        ip = Ip_tool.get_ip()
        # 爱奇艺平台
        plat_type = 1
        create_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        field = ['Fstat_num']
        where = "Fip_info='%s' and Fplat_type='%s' and Ftask_state='%s' and Fcreate_time='%s'" % (ip, plat_type, status_code, create_time)
        result = self.task_stat_db.query(field, where)
        if result:
            stat_num = int(result[0].get('Fstat_num'))
            stat_num += 1
            task = {
                'Fstat_num': stat_num,
                'Fmodify_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            self.task_stat_db.update(task, where)
        else:
            task = {
                'Fip_info': ip,
                'Fplat_type': plat_type,
                'Ftask_state': status_code,
                'Fstat_num': 1,
                'Fcreate_time': create_time,
                'Fmodify_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            self.task_stat_db.insert(task)
        self.task_stat_db.commit()

    # 字符串转md5
    def str2md5(self, url):
        m = hashlib.md5()
        m.update(url.encode('utf-8'))
        return m.hexdigest()
