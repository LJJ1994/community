__author__ = 'LJJ'
__date__ = '2019/9/19 下午1:20'

from flask import jsonify
from . import api


@api.route('/index')
def index():
    return jsonify({"code":200, "msg": "okkkk"})
