__author__ = 'LJJ'
__date__ = '2019/9/24 上午7:36'

import random
import re
import base64

from sqlalchemy.exc import IntegrityError
from flask import current_app, jsonify, make_response, request, session, g

from community.utils.response_code import RET
from community import redis_store, db
from community.models import User, Post
from community.api import api
from community import constans
from community.task.sms.tasks import send_sms
from community.utils.image_storage import storage
from community.constans import QINIU_DOMIN_PREFIX
from .auth import token_auth


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
    req_dict = request.get_json()
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
    user = User(phone=mobile, nick_name="笨笨猪" + str(random.randint(1, 99999)))
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


@api.route('/test', methods=['POST'])
@token_auth.login_required
def test():
    return jsonify(code=200, msg='测试token')


@api.route("/users/signin", methods=["POST"])
def login():
    """
    用户登录
    :param 手机号, 密码, json
    """
    req_dict = request.get_json()
    if req_dict is None:
        return jsonify(errno=RET.PARAMERR, errmsg="无参数")
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    print('mobile: %s password: %s' % (mobile, password))
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
    # session["name"] = mobile
    # session["mobile"] = mobile
    # session["user_id"] = user.id

    access_token = user.get_jwt()
    data = {
        "access_token": access_token,
        "data": user.to_dict()
    }
    print(access_token)
    return jsonify(errno=RET.OK, errmsg="登录成功", data=data)


@api.route("/users/<int:user_id>", methods=["GET"])
@token_auth.login_required
def get_user_info(user_id):
    """
    获取用户信息, 在登录情况下获取的用户信息, 还有未登录的情况,
    :param user_id:
    :return: json
    """
    user = g.current_user
    if not user:
        return jsonify(errno=RET.USERERR, errmsg='当前未登录')
    if user_id is None:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不存在", data="")
    try:
        other = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="数据库查询失败", data="")

    is_followed = False
    if other in user.followed:
        is_followed = True
    data = other.to_dict()

    # 获取个人详情页的所有帖子,按时间进行排序，发表最早的在前面
    posts = []
    post_list = Post.query.filter_by(user_id=other.id).order_by(Post.create_time.desc()).all()
    for post in post_list:
        posts.append(post.to_dict())
    data["post_list"] = posts
    data['is_followed'] = is_followed
    return jsonify(errno=RET.OK, errmsg="成功", data=data)


@api.route("/users/<int:user_id>/edit", methods=['POST'])
@token_auth.login_required
def user_edit_profile(user_id):
    """
    修改用户信息
    :param user_id:
    :arg { username, signature, value }  # value的值, 1：男 2：女 3：外星人
    :return:
    """
    import json
    try:
        user = User.query.filter_by(id=int(user_id)).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.USERERR, errmsg="用户参数错误", data='')

    req_dict = request.get_json()
    username = req_dict.get('username')
    signature = req_dict.get("signature")
    value = str(req_dict.get('value'))
    print('value: %s' % value)

    if not all([username, signature, value]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整", data='')

    gender_dict = {
        '1': 'MAN',
        '2': 'WOMAN',
        '3': 'Aliens'
    }

    user.nick_name = username
    user.signature = signature
    user.gender = gender_dict.get(value)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='保存数据库失败', data='')
    return jsonify(errno=RET.OK, errmsg='操作成功', data=user.to_dict())


@api.route('/users/avatar', methods=['POST'])
@token_auth.login_required
def edit_user_avatar():
    """
    修改用户头像
    :return: {avatar_url: str}
    """
    user = g.current_user
    print('*'*20)
    print(user)
    if user is None:
        return jsonify(errno=RET.USERERR, errmsg='用户未登录', data='')
    try:
        avatar = request.files.get('avatar').read()
        print('/'*20)
        print(avatar)
    except Exception as e:
        current_app.logger.error(e)
        jsonify(errno=RET.PARAMERR, errmsg='参数缺失', data='')

    try:
        key = storage(avatar)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传第三方异常', data='')

    user.avatar_url = key
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='保存头像失败', data='')
    data = {
        'avatar_url': QINIU_DOMIN_PREFIX + key
    }
    return jsonify(errno=RET.OK, errmsg='上传成功', data=data)


@api.route('/users/follow', methods=['POST'])
@token_auth.login_required
def user_follow():
    """
    用户执行关注操作
    :return: success or failed
    """
    user = g.current_user
    user_id = request.get_json().get('user_id')
    if not int(user_id):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        other = User.query.get(user_id)  # other指要关注的用户
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询该用户失败')

    if user == other:
        return jsonify(errno=RET.USERERR, errmsg='不能关注自己')

    if other in user.followed:
        return jsonify(errno=RET.USERERR, errmsg='该用户已关注过')
    user.followed.append(other)
    db.session.add(user)
    db.session.commit()

    # 这里有个关注发送通知
    data = {
        'followed_id': other.id,
        'followed_name': other.nick_name
    }
    return jsonify(errno=RET.OK, errmsg='关注成功', data=data)


@api.route('/users/unfollow', methods=['POST'])
@token_auth.login_required
def user_unfollow():
    """
    取消关注用户操作
    :return: success or failed
    """
    user = g.current_user
    req_dict = request.get_json()
    other_id = req_dict.get('user_id')
    if not int(other_id):
        return jsonify(errno=RET.PARAMERR, errmsg='参数有误')
    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据查询失败')
    if other not in user.followed:
        return jsonify(errno=RET.USERERR, errmsg='该用户没被关注过')
    user.followed.remove(other)
    db.session.add(user)
    db.session.commit()

    return jsonify(errno=RET.OK, errmsg='取关成功')
