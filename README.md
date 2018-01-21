Job-Data-Mining
========
招聘信息数据挖掘，致力于从各大求职网站挖掘出有用信息
这些招聘信息来自中国各大互联网：智联、拉勾、51jobs等等

Job-Data-Mining, this project is dedicated to find useful information from jobs posted on varies websites
such as zhilian, lagou, 51jobs and so on.

- _Scroll down for English documentation._

效果说明
========
 * 爬取元数据：职位1：数据工程师   职位2：AI工程师   职位3：后台开发工程师   职位4：产品经理   职位5：产品销售 
 * 职位聚类：互联网后台类（职位1，职位2，职位3）业务类（职位4，职位5）
 * 关键词聚类：互联网后台类（服务器、机器学习、大数据、推荐系统）业务类（产品设计、视觉设计、交流能力、市场分析） 
 * 本项目预期效果：任何求职者能够通过聚类找到自己理想工作所属类别，并利用技能关键词了解技能要求，最优化分配自己的学习资源


基础环境搭建流程
=======
* 对个人用户来说，建议使用ubuntu系统，可以大幅度简化安装。不建议用centos
* 本人系统信息:Linux ubuntu 4.13.0-26-generic #29~16.04.2-Ubuntu SMP Tue Jan 9 22:00:44 UTC 2018 x86_64 x86_64 x86_64 GNU/Linux

* 安装python3：
    * sudo apt-get install python3
    * sudo apt-get install python3-pip pip3用于简易安装python第三方

* 安装mysql服务器，客户端
    * sudo apt-get install mysql-server
    * sudo apt-get isntall mysql-client
    * sudo apt-get install libmysqlclient-dev

* 安装python3第三方
    * pip3 install mysql-connector-python python的mysql客户端
    * pip3 install scrapy # 高并发爬虫框架
    * pip3 install gensim # 主题模型

* 创建开发目录
    * 用$username指代用户名
    * 将JOB-DATA-MINING文件夹拷贝至/home/$username/下

* 将工程文件加入环境变量
    * 在当前用户的根目录下的.bashrc文件最后行加入
    * export PYTHONPATH=:/home/$username/JOB-DATA-MINING/job_data_mining
    * 执行source .bashrc使之生效
    * 可用 echo $PYTHONPATH 确定./bashrc是否生效
    
* 安装结巴分词器
    * https://github.com/fxsjy/jieba处下载结巴工程
    * 将jieba-master下的jieba文件夹放置于job-data-mining目录下

* 建立数据库
    * 用$password指代mysql密码
    * shell指令执行：
      mysql -uroot -ppassword < /home/$username/JOB-DATA-MINING/sql_files/zhilian_tables.sql

过程方法
========
* 采用Scrapy框架爬取数据，解析与入库逻辑可配置，用户不需要深度参与爬虫开发
* 关键词提取采用SNS挖掘方法提取新词，随后采用结巴分词器进行分词
* 主题提取采用LDA或者Word2Vect方法

--------未完待续--------