__author__ = 'LJJ'
__date__ = '2019/9/27 下午5:18'

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


@api.route('/post/publish', methods=['POST'])
@token_auth.login_required
def publish_post():
    """
    用户发表帖子
    :param { image || content || category}
    :return: data
    """

    user = g.current_user
    images = request.files.getlist('file')
    category_id = request.form.get('category_id')
    content = request.form.get('content')

    print('*'*20)
    print(images)
    print(category_id)
    print(content)
    print('*'*20)

    # 用户发帖子时有6种情况
    # 1. 在选择话题分类的情况下
    #   1) 只发文字
    #   2) 只发图片
    #   3) 两者都发
    # 2. 在没有选择话题分类的情况下
    #   1) 只发文字
    #   2) 只发图片
    #   3) 文字和图片都发

    # 判断前端是否传送image过来
    has_image = True
    for img in images:
        if not img.filename:
            has_image = False

    # 如果都没发送content or image, 直接返回
    # 实际上这是由前端来判断的, 我懒得写了.
    if not any([content, has_image]):
        return jsonify(errno=RET.PARAMERR, errmsg='请填写内容再发送过来', data='')
    if category_id:
        try:
            category = Category.query.filter_by(id=category_id).first()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DATAERR, errmsg='查询该分类失败', data='')
        if category is None:
            return jsonify(errno=RET.DATAEXIST, errmsg='该分类不存在!', data='')
        if content and has_image:
            image_url = []
            try:
                for image in images:
                    key = storage(image.read())
                    image_url.append(key)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg='第三方上传异常', data='')

            try:
                post = Post(user_id=user.id, content=content, category_id=category_id)
                db.session.add(post)
                db.session.commit()
                print('post_id: %s' % post.id)
                for url in image_url:
                    images = Images(post_id=post.id, url=url)
                    db.session.add(images)
                    db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg='保存数据失败!', data='')
            return jsonify(errno=RET.OK, errmsg='发表成功!')
        elif content and (not has_image):
            try:
                post = Post(user_id=user.id, content=content, category_id=category_id)
                db.session.add(post)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg='保存数据失败!', data='')
            return jsonify(errno=RET.OK, errmsg='发表成功!')
        else:
            image_url = []
            try:
                for image in images:
                    key = storage(image.read())
                    image_url.append(key)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg='第三方上传异常', data='')
            try:
                post = Post(user_id=user.id, category_id=category_id)
                db.session.add(post)
                db.session.commit()
                for url in image_url:
                    images = Images(post_id=post.id, url=url)
                    db.session.add(images)
                    db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg='保存数据失败!', data='')
            return jsonify(errno=RET.OK, errmsg='发表成功!')
    else:
        if content and has_image:
            image_url = []
            try:
                for image in images:
                    key = storage(image.read())
                    image_url.append(key)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg='第三方上传异常', data='')

            try:
                post = Post(user_id=user.id, content=content)
                db.session.add(post)
                db.session.commit()
                for url in image_url:
                    images = Images(post_id=post.id, url=url)
                    db.session.add(images)
                    db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg='保存数据失败!', data='')
            return jsonify(errno=RET.OK, errmsg='发表成功!')
        elif content and (not has_image):
            try:
                post = Post(user_id=user.id, content=content)
                db.session.add(post)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg='保存数据失败!', data='')
            return jsonify(errno=RET.OK, errmsg='发表成功!')
        else:
            image_url = []
            try:
                for image in images:
                    key = storage(image.read())
                    image_url.append(key)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify(errno=RET.THIRDERR, errmsg='第三方上传异常', data='')
            try:
                post = Post(user_id=user.id)
                db.session.add(post)
                db.session.commit()
                for url in image_url:
                    images = Images(post_id=post.id, url=url)
                    db.session.add(images)
                    db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify(errno=RET.DATAERR, errmsg='保存数据失败!', data='')
            return jsonify(errno=RET.OK, errmsg='发表成功!')


@api.route('/post/<int:user_id>', methods=['GET'])
def get_user_post(user_id):
    """
    获取某个用户的发表所有帖子
    :param user_id:
    :return:
    """
    if not int(user_id):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    try:
        user = User.query.filter_by(id=user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询数据库失败', data='')
    if not user:
        return jsonify(errno=RET.NODATA, errmsg='该用户不存在!', data='')
    try:
        posts = Post.query.filter_by(user_id=user.id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询数据库失败', data='')
    data_dict = []
    for post in posts:
        data_dict.append(post.to_dict())
    return jsonify(errno=RET.OK, errmsg='成功', data=data_dict)


@api.route('/post/delete/<int:post_id>', methods=['POST'])
@token_auth.login_required
def delete_post(post_id):
    """
    删除某个帖子
    :param post_id
    :return:
    """
    if int(post_id) is None:
        return jsonify(errno=RET.PARAMERR, errmsg='请求参数错误')
    try:
        post = Post.query.filter_by(id=post_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='要删除的帖子不存在', data='')
    try:
        db.session.delete(post)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='删除失败', data='')
    return jsonify(errno=RET.OK, errmsg='删除成功', data='')
