CREATE DATABASE db_job;
USE db_job;

CREATE TABLE `t_failed_task` (
  `Fauto_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务ID，自增',
  `Fcrawler_name` varchar(64) NOT NULL DEFAULT '' COMMENT '爬虫名',
  `Fcall_back` varchar(64) NOT NULL DEFAULT '' COMMENT '回调函数名',
  `Fcookies` varchar(256) NOT NULL DEFAULT '' COMMENT 'Cookie字符串',
  `Fdont_filter` tinyint(10) NOT NULL DEFAULT '0',
  `Fencoding` varchar(64) NOT NULL DEFAULT '' COMMENT '请求编码',
  `Ferrback` tinyint(20) NOT NULL DEFAULT '0',
  `Fflags` varchar(1024) NOT NULL DEFAULT '',
  `Fheaders` varchar(1024) NOT NULL DEFAULT '' COMMENT '报头信息',
  `Fmeta` varchar(1024) NOT NULL DEFAULT '' COMMENT '请求信息',
  `Fmethod` varchar(64) NOT NULL DEFAULT '' COMMENT '请求类型',
  `Fpriority` bigint(20) NOT NULL DEFAULT '0' COMMENT '优先级',
  `Furl` varchar(1024) NOT NULL DEFAULT '' COMMENT '请求URL',
  `Fstate` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0-初始化 1-任务成功,2-任务失败',
  `Fretry_times` tinyint(4) NOT NULL DEFAULT '0',
  `Fcreate_time` datetime NOT NULL,
  `Fmodify_time` datetime NOT NULL,
  PRIMARY KEY (`Fauto_id`),
  KEY `idx_callback_name` (`Fcrawler_name`,`Fcall_back`),
  KEY `idx_state` (`Fstate`),
  KEY `idx_url` (`Furl`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `t_zhilian_task` (
  `Ftask_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务ID，自增',
  `Fcategory` varchar(64) NOT NULL DEFAULT '0' COMMENT '任务类别',
  `Ftask_url` varchar(1024) NOT NULL DEFAULT '' COMMENT '任务URL',
  `Fstate` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0-初始化 1-任务成功,2-任务失败',
  `Fcreate_time` datetime NOT NULL,
  `Fmodify_time` datetime NOT NULL,
  PRIMARY KEY (`Ftask_id`),
  KEY `idx_task_url` (`Ftask_url`),
  KEY `idx_state` (`Fstate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `t_zhilian_detail` (
  `Fauto_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务ID，自增',
  `Fjob_title` varchar(128) NOT NULL DEFAULT '' COMMENT '工作标题',
  `Fjob_salary` varchar(128) NOT NULL DEFAULT '' COMMENT '工作报酬',
  `Fjob_pubdate` varchar(128) NOT NULL DEFAULT '' COMMENT '工作发布日期',
  `Fjob_experience` varchar(64) NOT NULL DEFAULT '' COMMENT '工作经验要求',
  `Fjob_count` varchar(64) NOT NULL DEFAULT '' COMMENT '工作岗位数',
  `Fjob_location` varchar(128) NOT NULL DEFAULT '' COMMENT '工作地点',
  `Fjob_type` varchar(128) NOT NULL DEFAULT '' COMMENT '工作性质',
  `Fjob_minreq` varchar(64) NOT NULL DEFAULT '' COMMENT '工作最低要求',
  `Fjob_url` varchar(256) NOT NULL DEFAULT '' COMMENT '工作主页',
  `Fjob_name` varchar(128) NOT NULL DEFAULT '' COMMENT '工作名称',
  `Fjob_summary` text NOT NULL COMMENT '工作描述',
  `Fcorp_name` varchar(128) NOT NULL DEFAULT '' COMMENT '公司名称',
  `Fcorp_size` varchar(64) NOT NULL DEFAULT '' COMMENT '公司规模',
  `Fcorp_type` varchar(128) NOT NULL DEFAULT '' COMMENT '公司性质',
  `Fcorp_category` varchar(128) NOT NULL DEFAULT '' COMMENT '公司类别',
  `Fcorp_url` varchar(256) NOT NULL DEFAULT '' COMMENT '公司主页',
  `Fcorp_location` varchar(128) NOT NULL DEFAULT '' COMMENT '公司地址',
  `Fcorp_summary` text NOT NULL COMMENT '工作名称',
  `Flstate` tinyint(4) NOT NULL DEFAULT '0' COMMENT '1-正常 2-删除',
  `Fcreate_time` datetime NOT NULL,
  `Fmodify_time` datetime NOT NULL,
  PRIMARY KEY (`Fauto_id`),
  KEY `idx_lstate` (`Flstate`),
  KEY `idx_modify_time` (`Fmodify_time`),
  KEY `idex_job_url` (`Fjob_url`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
