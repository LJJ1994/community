__author__ = 'LJJ'
__date__ = '2019/9/28 下午6:09'

import random
import re
import base64

from sqlalchemy.exc import IntegrityError
from flask import current_app, jsonify, make_response, request, session, g

from community.utils.response_code import RET
from community import redis_store, db
from community.models import User, Post, Images, Category
from community.api import api
from community import constans
from community.task.sms.tasks import send_sms
from community.utils.image_storage import storage
from community.constans import QINIU_DOMIN_PREFIX
from .auth import token_auth


@api.route('/category', methods=['POST'])
def add_category():
    """
    添加话题分类
    data: name introduce
    :return:
    """
    req_dict = request.get_json()
    name = req_dict.get("name")
    introduce = req_dict.get("introduce")

    if not all([name, introduce]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失', data='')

    exist = Category.query.filter_by(name=name).first()
    if exist:
        return jsonify(errno=RET.DATAEXIST, errmsg='该分类已存在', data='')

    try:
        category = Category(name=name, introduce=introduce)
        db.session.add(category)
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DATAERR, errmsg='保存数据失败', data='')
    return jsonify(errno=RET.OK, errmsg='添加成功')


@api.route("/category/<int:category_id>", methods=['GET'])
def get_category(category_id):
    """
    获取某个具体的分类
    :param category_id
    :return category_dict
    """
    if not int(category_id):
        return jsonify(errno=RET.PARAMERR, errmsg='参数异常')
    try:
        category = Category.query.filter_by(id=category_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据库查询异常')
    data = category.to_base()
    return jsonify(errno=RET.OK, errmsg='OK', data=data)


@api.route("/category", methods=['GET'])
def get_category_list():
    """
    获取所有分类
    :return: dict
    """
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据库异常', data='')

    category_list = []
    for category in categories:
        category_list.append(category.to_base())
    return jsonify(errno=RET.OK, errmsg='成功', data=category_list)
