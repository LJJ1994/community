__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:17'


from flask import Blueprint
from flask_cors import CORS


api = Blueprint('api', __name__)
CORS(api)

from . import index, auth, token, register, post, category
