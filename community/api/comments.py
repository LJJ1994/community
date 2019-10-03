__author__ = 'LJJ'
__date__ = '2019/10/3 下午12:36'

from . import api
from .auth import token_auth


@api.route('/comments/', methods=['[POST'])
@token_auth.login_required
def comment_one_post():
    """
    评论某个帖子
    :param post_id, content
    :return:
    """
    pass
