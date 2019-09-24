__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:36'

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


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
tb_user_collection = db.Table(
    "user_collection",
    db.Column('user_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 用户编号
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),  # 帖子编号
    db.Column('create_time', db.DateTime, default=datetime.now),  # 帖子创建时间
)


class User(BaseModel, db.Model):
    """用户表"""
    __tablename__ = 'cm_user'

    id = db.Column(db.Integer, primary_key=True)
    nick_name = db.Column(db.String(32), unique=True, default=USER_DEFAULT_NICK_NAME, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    signature = db.Column(db.String(512))
    location = db.Column(db.String(20), default=USER_DEFAULT_LOCATION)
    score = db.Column(db.Integer, default=0)
    avatar_url = db.Column(db.String(512))
    collection_post = db.relationship('Post', secondary=tb_user_collection, lazy='dynamic')
    post_list = db.relationship('Post', backref='user', lazy='dynamic')
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
