__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:17'


from flask import Blueprint


api = Blueprint('api', __name__)

from . import index, auth, token, register
