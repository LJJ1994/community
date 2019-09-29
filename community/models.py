__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:36'

from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from . import db
from .constans import USER_DEFAULT_LOCATION, QINIU_DOMIN_PREFIX, USER_DEFAULT_AVATAR


class BaseModel(object):
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录创建时间
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录更新时间
    delete_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)  # 记录删除时间


# 用户和粉丝的虚拟表
tb_user_follows = db.Table(
    "user_fans",
    db.Column('follower_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 粉丝id
    db.Column('followed_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 被关注的人id
    db.Column('create_time', db.DateTime, default=datetime.now)
)


# 用户收藏表, 建立用户和收藏帖子的多对多关系
tb_user_post = db.Table(
    "user_collection",
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
    collection_post = db.relationship('Post', secondary=tb_user_post, lazy='dynamic')  # 用户收藏的帖子
    post_list = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    followers_count = db.Column(db.Integer, default=0)  # 粉丝数
    followed_count = db.Column(db.Integer, default=0)  # 关注数
    # 用户所有的粉丝，添加了反向引用followed，代表用户都关注了哪些人
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
            "avatar_url": QINIU_DOMIN_PREFIX + self.avatar_url if self.avatar_url else USER_DEFAULT_AVATAR,
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
            current_app.logger.error(e)
            return None
        return User.query.get(payload.get('user_id'))


class Post(BaseModel, db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('cm_category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'))
    comments = db.relationship('Comment', lazy='dynamic')  # 当前帖子的所有评论
    images = db.relationship('Images', backref='post')  # 帖子信息表

    def to_dict(self):
        post_dict = {
            "post_id": self.id,
            "content": self.content,
            "clicks": self.clicks,
            "category_id": self.category_id,
            "user_id": self.user_id,
            "comments": ''
        }
        img_url = []
        for img in self.images:
            img_url.append(QINIU_DOMIN_PREFIX + img.url)  # 这里存储的是七牛返回过来的key
        post_dict["img_url"] = img_url
        return post_dict


class Images(BaseModel, db.Model):
    """帖子 图片"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    url = db.Column(db.String(256), nullable=False)


class PostLike(BaseModel, db.Model):
    """评论点赞"""
    __tablename__ = "post_like"
    comment_id = db.Column("comment_id", db.Integer, db.ForeignKey("post.id"), primary_key=True)  # 评论编号
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("comment.id"), primary_key=True)  # 用户编号


class Comment(BaseModel, db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # 父评论id
    parent = db.relationship('Comment', remote_side=[id])  # 自关联
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    # images = db.relationship('Images', backref='comment')


class CommentLike(BaseModel, db.Model):
    """评论点赞"""
    __tablename__ = "comment_like"
    comment_id = db.Column("comment_id", db.Integer, db.ForeignKey("comment.id"), primary_key=True)  # 评论编号
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("cm_user.id"), primary_key=True)  # 用户编号


class Category(BaseModel, db.Model):
    """话题分类"""
    __tablename__ = 'cm_category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(52), nullable=False)
    introduce = db.Column(db.String(256), default="我是话题简介")
    post_list = db.relationship('Post', backref='category', lazy='dynamic')
    comment_count = db.Column(db.Integer, default=0)  # 话题数量

    def to_base(self):
        return {
            "category_id": self.id,
            "name": self.name,
            "comment_count": self.comment_count,
            "introduce": self.introduce
        }
