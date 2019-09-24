__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:31'

# --*-- coding:utf-8 --*--

from werkzeug.routing import BaseConverter
import functools
from flask import session, g, jsonify
from community.utils.response_code import RET


# 定义正则转换器
class ReConvertor(BaseConverter):
    """"""
    def __init__(self, url_map, regex):
        super(ReConvertor, self).__init__(url_map)
        self.regex = regex


# 定义验证登录状态的装饰器
def required_login(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        # 判断用户登录状态
        user_id = session.get("user_id")

        # 如果用户登录,则执行视图函数
        if user_id is not None:
            # 将user_id保存到ｇ对象,后面可以在视图函数访问到.
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    return wrapper
