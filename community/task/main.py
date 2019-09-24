# --*-- coding:utf-8 --*--

from celery import Celery
from community.task import config

# 配置celery对象
celery_app = Celery("community")

# 引入配置信息
celery_app.config_from_object(config)

# 自动加载发送短信的异步任务
celery_app.autodiscover_tasks(["community.task.sms"])

# celery开启命令, 在项目主目录下:
# celery -A community.task.main worker -l info
#
# CELERY模型-----------
#
#                                                       这里是真正执行任务的一方,即处理函数在这里编写
#                                 任务队列(broker)      任务处理者(worker)
#  客户端(发送请求给服务端)-------->1.任务1 ----------->   多进程(默认),协程
#   定义任务和发布任务             2. 任务2                 app = celery()
#                                3. 任务3                 @app.tacsk
#   app = Celery()                                        def send_sms():
#
#   @app.task                   ###################     在这里开启celery服务
#   def send_sms():             # redis处理后的结果 #
#                               ###################
#   发布任务
#   send_sms.delay()
#
