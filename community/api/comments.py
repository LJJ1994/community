__author__ = 'LJJ'
__date__ = '2019/10/3 下午12:36'

from flask import request, g, jsonify, current_app
from . import api
from .auth import token_auth
from community.utils.response_code import RET
from community.models import Comment, Post, User
from community import db


@api.route('/comments', methods=['POST'])
@token_auth.login_required
def comment_one_post():
    """
    评论某个帖子
    :param post_id, content
    :return:
    """
    user = g.current_user
    req_dict = request.get_json()
    post_id = req_dict.get('post_id', None)
    content = req_dict.get('content', None)
    if not all([post_id, content]):
        return jsonify(errno=RET.PARAMERR, errmsg='评论不能为空', data='')
    print('post_id: %s' % post_id)
    print(content)
    try:
        comment = Comment(user_id=user.id, post_id=post_id, content=content)
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='保存数据库出错', data='')
    return jsonify(errno=RET.OK, errmsg='成功')


@api.route('/comments/<int:comment_id>', methods=['GET'])
@token_auth.login_required
def get_comment_detail(comment_id):
    """
    获取某个评论的详情内容
    :param comment_id
    :return: dict
    """
    user = g.current_user
    if not int(comment_id):
        return jsonify(errno=RET.PARAMERR, errmsg='评论id错误', data='')

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询数据库失败')

    data = comment.to_detail_dict()
    other = comment.author
    user_followed = {
        'is_followed': 0
    }
    if user:
        if other.is_followed_by(user):
            user_followed = {
                'is_followed': 1
            }
    data.update(user_followed)
    if user:
        if comment.is_liked_by(user):
            comment.liked_by(user)
            data.update({'is_liked': 1})  # 点赞为1 未未点赞为0

    return jsonify(errno=RET.OK, errmsg='成功', data=data)


@api.route('/comments/reply', methods=['POST'])
@token_auth.login_required
def reply_comment():
    """
    回复评论
    :param post_id, comment_id
    :return:
    """
    user = g.current_user
    req_dict = request.get_json()
    post_id = req_dict.get('post_id')
    comment_id = req_dict.get('comment_id')  # 父评论id
    content = req_dict.get('content')

    print('post_id: %s' % post_id)
    print('comment_id %s' % comment_id)
    print('content %s' % content)
    if not all([int(post_id), int(comment_id), str(content)]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    try:
        post = Post.query.get(post_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询帖子出错')
    if not post_id:
        return jsonify(errno=RET.DATAERR, errmsg='该帖子不存在')

    try:
        parentComment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='查询父评论失败', data='')

    try:
        comment = Comment(post_id=post_id,
                          parent_id=comment_id,
                          user_id=user.id,
                          content=content)
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='数据保存失败', data='')
    return jsonify(errno=RET.OK, errmsg='评论成功', data='')
