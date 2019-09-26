__author__ = 'LJJ'
__date__ = '2019/9/25 下午4:26'

from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from community import db
from community.models import User


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username, password):
    """用于检查用户提供的用户名和密码"""
    user = User.query.filter_by(phone=username).first()
    if user is None:
        return False
    g.current_user = user
    return user.check_password(password)


@basic_auth.error_handler
def basic_auth_error():
    """返回认证失败状态码"""
    return jsonify({'code': 401, 'msg': '登录失败'})


@token_auth.verify_token
def verify_token(token):
    '''用于检查用户请求是否有token，并且token真实存在，还在有效期内'''
    g.current_user = User.verify_jwt(token) if token else None
    if g.current_user:
        # 每次认证通过后（即将访问资源API），更新 last_seen 时间
        g.current_user.update_token()
        db.session.commit()
    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    '''用于在 Token Auth 认证失败的情况下返回错误响应'''
    return jsonify({'code': 401, 'msg': 'token认证失败'})
