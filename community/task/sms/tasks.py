# --*-- coding:utf-8 --*--

from community.task.main import celery_app
from community.libs.yuntongxun.sms import CCP


@celery_app.task
def send_sms(to, data, temp_id):
    """发送短信的异步任务"""
    ccp = CCP()
    try:
        result = ccp.send_template_sms(to, data, temp_id)
    except Exception as e:
        result = -2
    return result
