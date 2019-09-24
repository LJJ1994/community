__author__ = 'LJJ'
__date__ = '2019/9/24 上午7:36'

import random
import re
import base64

from sqlalchemy.exc import IntegrityError
from flask import current_app, jsonify, make_response, request, session

from community.utils.response_code import RET
from community import redis_store, db
from community.models import User
from community.api import api
from community import constans
from community.task.sms.tasks import send_sms


# "/api/v1.0/sms_codes/<mobile>"
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """"获取短信验证码"""
    # 判断该手机号的操作记录，如果60秒内有之前的记录，则判断为频繁操作
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请稍后再试!")

    # 判断手机是否存在
    try:
        user = User.query.filter_by(phone=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据库查询异常")
    else:
        # 该手机号已存在
        if user is not None:
            return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")

    # 如果手机号不存在，则生成验证码
    sms_code = "%04d" % random.randint(0, 999999)

    # 保存真实验证码到redis
    try:
        redis_store.setex("sms_code_%s" % mobile, constans.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给该手机的记录，防止用户在６０秒内再次发送请求
        redis_store.setex("send_sms_code_%s" % mobile, constans.SEND_SMS_CODE_REDIS_EXPIRES, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="保存手机验证码失败！")

    # 发送短信
    # try:
    #     ccp = CCP()
    #     result = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送异常")
    # 返回值
    # if result == 0:
    #     return jsonify(errno=RET.OK, errmsg="发送成功!")
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送失败！")

    # 使用celery异步发送短信,delay函数调用后立即返回
    result_obj = send_sms.delay(mobile, [sms_code, int(constans.SMS_CODE_REDIS_EXPIRES / 60)], 1)
    ret = result_obj.get()
    print("ret = %s" % ret)
    return jsonify(errno=RET.OK, errmsg="发送成功")


@api.route("/users/signup", methods=["POST"])
def register():
    """注册接口
        请求的参数: 手机号,　短信验证码,　密码, 确认密码
    """
    # 获取请求的json, 返回字典
    import json
    req_dict = request.get_json()
    print(req_dict)
    mobile = req_dict.get("mobile")
    sms_code = str(req_dict.get("sms_code"))
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 校验手机号
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码验证不正确")

    # 从redis取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="读取真实短信验证码异常")

    # 检查短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码已过期")

    # 删除短信验证码信息，防止用户重复校正
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写的短信验证码是否正确
    print("real:%s , send: %s" % (real_sms_code, sms_code.encode('UTF-8')))
    real_sms_code_str = real_sms_code.decode("UTF-8")

    if real_sms_code_str != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")

    # 保存用户的数据到数据库
    user = User(phone=mobile)
    # 在这里设置password,password在数据库模型用已经定义好,包括加密处理,这里的password是一个类属性，可以set,也可以get
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    # 这里跑出一个数据库异常
    except IntegrityError as e:
        # 数据库操作错误后的回滚
        db.session.rollback()
        # 表示手机号重复
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已存在")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库异常")

    # 保存登录状态到session
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/users/signin", methods=["POST"])
def login():
    """
    用户登录
    :param 手机号, 密码, json
    """

    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 参数完整性校验
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 手机号格式校验
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 判断错误次数是否超过限制，如果超过则返回
    # access_nums 记录请求次数，并放入redis中
    # user_ip 为用户ip
    user_ip = request.remote_addr
    print("romote_addr", user_ip)
    try:
        access_nums = redis_store.get("access_num_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constans.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请过段时间再试")

    # 从数据库中根据手机号查询用户的数据对象
    try:
        user = User.query.filter_by(phone=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="获取用户信息失败")

    # 数据库密码和用户发送过来的密码进行校验
    if user is None or not user.check_password(password):
        # 校验失败,　记录错误信息,　然后返回
        try:
            # 对access_num_user_ip进行加１操作, 如果数据不存在, 则初始化为１
            redis_store.incr("access_num_%s" % user_ip)
            redis_store.expire("access_num_%s" % user_ip, constans.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

    # 如果校验相同,则保存在session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """检查用户登录状态"""

    # 通过检查session里面的用户名name是否存在
    name = session.get("name")
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def logout():
    """登出操作"""

    # 清楚session数据
    session.clear()
    return jsonify(errno=RET.OK, errmsg="OK")
