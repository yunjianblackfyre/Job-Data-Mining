#   AUTHOR: Sibyl System
#     DATE: 2018-04-20
#     DESC: status code 
#           for task state

#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import IntEnum

class StatusCode(IntEnum):
    STAT_TASK_INIT =         0 # 任务初始
    STAT_TASK_START =        1 # 任务开始
    STAT_TASK_SUCCESS =      2 # 任务成功
    STAT_TASK_RETRY =        3 # 任务重试中
    STAT_TASK_FAILED =       4 # 任务失败
    STAT_DETAIL_INIT =       0 # 详情初始
    STAT_DETAIL_IMGSTART =   1 # 详情图片下载开始
    STAT_DETAIL_IMGREADY =   2 # 详情图片下载完成


if __name__ == '__main__':
    print(StatusCode.STAT_FAILED.value)
    print(StatusCode.__getitem__('STAT_FAILED'))
