
from flask.blueprints import Blueprint
from flask import current_app, make_response
from flask_wtf import csrf
import requests

# 提供静态文件的蓝图
html = Blueprint("html", __name__)


# 渲染html
@html.route('/<re(".*"):html_file_name>')
def get_html(html_file_name):
    if not html_file_name:
        html_file_name = "index.html"
    if html_file_name != "favicon.ico":
        html_file_name = "html/" + html_file_name

    # 设置csrf防护机制
    csrf_token = csrf.generate_csrf()

    resp = make_response(current_app.send_static_file(html_file_name))
    resp.set_cookie("csrf_token", csrf_token)
    return resp
