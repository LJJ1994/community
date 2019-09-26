__author__ = 'LJJ'
__date__ = '2019/9/25 下午4:36'

from flask import jsonify, g
from community import db
from community.api import api
from community.api.auth import basic_auth


@api.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_jwt()
    # 每次用户登录（即成功获取 JWT 后），更新 last_seen 时间
    g.current_user.update_token()
    db.session.commit()
    return jsonify({'token': token})
