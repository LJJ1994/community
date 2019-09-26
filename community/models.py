__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:36'

from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from . import db
from .constans import USER_DEFAULT_NICK_NAME, USER_DEFAULT_LOCATION


class BaseModel(object):
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录更新时间
    delete_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录删除时间


# 用户和粉丝的虚拟表
tb_user_follows = db.Table(
    "user_fans",
    db.Column('follower_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 粉丝id
    db.Column('followed_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 被关注的人id
)


# 用户和帖子的虚拟表
tb_user_post = db.Table(
    "user_post",
    db.Column('user_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 用户编号
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),  # 帖子编号
    db.Column('create_time', db.DateTime, default=datetime.now),  # 帖子创建时间
)


class User(BaseModel, db.Model):
    """用户表"""
    __tablename__ = 'cm_user'

    id = db.Column(db.Integer, primary_key=True)
    nick_name = db.Column(db.String(32))
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    signature = db.Column(db.String(512))
    location = db.Column(db.String(20), default=USER_DEFAULT_LOCATION)
    score = db.Column(db.Integer, default=0)
    like = db.Column(db.Integer, default=0)  # 用户发表的帖子, 评论, 回复 所获得的点赞的总数
    avatar_url = db.Column(db.String(512))
    collection_post = db.relationship('Post', secondary=tb_user_post, lazy='dynamic')
    post_list = db.relationship('Post', backref='user', lazy='dynamic')
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    followers_count = db.Column(db.Integer, default=0)  # 粉丝数
    followed_count = db.Column(db.Integer, default=0)  # 关注数
    followers = db.relationship('User',
                                secondary=tb_user_follows,
                                primaryjoin=id == tb_user_follows.c.followed_id,
                                secondaryjoin=id == tb_user_follows.c.follower_id,
                                backref=db.backref('followed', lazy='dynamic'),
                                lazy='dynamic')
    gender = db.Column(
        db.Enum(
            "MAN",
            "WOMAN",
            "Aliens",
        ),
        default='Aliens'
    )

    @property
    def password(self):
        raise AttributeError(u"不能访问该属性")

    @password.setter
    def password(self, value):
        self.password_hash = generate_password_hash(value)

    def check_password(self, passwd):
        return check_password_hash(self.password_hash, passwd)

    def update_token(self):
        self.last_seen = datetime.now()
        db.session.add(self)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.nick_name,
            "phone": self.phone,
            "signature": self.signature,
            "location": self.location,
            "score": self.score,
            "avatar_url": "",
            "gender": self.gender,
            "like": self.like,
            "followers_count": self.followers_count if self.followers_count else 0,
            "followed_count": self.followed_count if self.followed_count else 0
        }

    # 给登录成功的用户颁发有时限的token
    def get_jwt(self, expire=60*60):
        now = datetime.now()
        payload = {
            'user_id': self.id,
            'name': self.nick_name,
            'exp': now + timedelta(expire),
            'iat': now
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    # 验证token
    @staticmethod
    def verify_jwt(token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
            algorithms=['HS256'])
        except (jwt.exceptions.ExpiredSignatureError,
                jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.DecodeError) as e:
            return None
        return User.query.get(payload.get('user_id'))


class Post(BaseModel, db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), nullable=False)
    content = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(256))
    category_id = db.Column(db.Integer, db.ForeignKey('cm_category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'))
    status = db.Column(db.Integer, default=0)  # 审核状态, 如果发的为视频，则需要审核，默认为0,1为正在审核，2为审核不通过
    reason = db.Column(db.String(256))  # 审核不通过原因
    comments = db.relationship('Comment', lazy='dynamic')  # 当前帖子的所有评论


class Comment(BaseModel, db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # 父评论id
    parent = db.relationship('Comment', remote_side=[id])  # 自关联
    like_count = db.Column(db.Integer, default=0)  # 点赞数


class CommentLike(BaseModel, db.Model):
    """点赞评论表"""
    __tablename = 'comment_like'
    comment_id = db.Column('comment_id', db.Integer, db.ForeignKey('comment.id'), primary_key=True)
    post_id = db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True)


class Category(BaseModel, db.Model):
    """话题分类"""
    __tablename__ = 'cm_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(52), nullable=False)
    post_list = db.relationship('Post', backref='category', lazy='dynamic')
