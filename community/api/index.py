__author__ = 'LJJ'
__date__ = '2019/9/19 下午1:20'

from flask import jsonify, render_template
from . import api


@api.route('/')
def index():
    return render_template("index.html")
