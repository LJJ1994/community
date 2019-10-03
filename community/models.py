__author__ = 'LJJ'
__date__ = '2019/9/19 上午9:36'

from time import time
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from . import db
from .constans import USER_DEFAULT_LOCATION, QINIU_DOMIN_PREFIX, USER_DEFAULT_AVATAR
from community.utils.time_format import time_since


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

# 用户点赞帖子
# 一个用户可以点赞多个帖子，一个帖子被多个用户点赞，多对多关系
post_like = db.Table(
    "post_like",
    db.Column('user_id', db.Integer, db.ForeignKey('cm_user.id'), primary_key=True),  # 用户id
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),  # 帖子id
    db.Column('create_time', db.DateTime, default=datetime.now)
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
    # followers表示用户所有的粉丝
    # 添加了反向引用followed，表示用户都关注了哪些人
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
            "followers_count": self.followers.count() if self.followers.count() else 0,
            "followed_count": self.followed.count() if self.followed.count() else 0
        }

    def to_index(self):
        posts = []
        post_list = self.post_list.order_by(Post.create_time.desc()).all()
        for post in post_list:
            posts.append(post.to_dict())

        user = self.to_dict()
        user["post_list"] = posts
        return user

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
    clicks = db.Column(db.Integer, default=0)  # 浏览数
    likers = db.relationship('User', secondary=post_like,
                              backref=db.backref('post_like', lazy='dynamic'), lazy='dynamic')  # 帖子和点赞他的人是多对多关系
    like_counts = db.Column(db.Integer, default=0)  # 帖子点赞数
    category_id = db.Column(db.Integer, db.ForeignKey('cm_category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'))
    comments = db.relationship('Comment', lazy='dynamic')  # 当前帖子的所有评论
    images = db.relationship('Images', backref='post')  # 帖子信息表

    def is_liked_by(self, user):
        '''判断用户 user 是否已经对该评论点过赞'''
        return user in self.likers

    def liked_by(self, user):
        '''点赞'''
        self.likers.append(user)

    def unliked_by(self, user):
        '''取消点赞'''
        self.likers.remove(user)

    def to_dict(self):
        post_dict = {
            "user_id": self.user_id,
            "username": User.query.filter_by(id=self.user_id).first().nick_name,
            "avatar_url": QINIU_DOMIN_PREFIX + User.query.filter_by(id=self.user_id).first().avatar_url,
            "post_id": self.id,
            "content": self.content,
            "clicks": self.clicks,
            "like_counts": self.like_counts,
            "comments_counts": self.comments.count(),  # 评论数
            "create_time": time_since(self.create_time),
            "likers_ids": [user.id for user in self.likers]  # 帖子点赞的用户id列表
        }

        # 获取image url
        img_url = []
        for img in self.images:
            img_url.append(QINIU_DOMIN_PREFIX + img.url)  # 这里存储的是七牛返回过来的key
        post_dict["img_url"] = img_url

        # 获取category
        # 前面业务逻辑中可能有: 用户发表帖子没有选择话题分类的情况
        if self.category_id:
            category = Category.query.filter_by(id=self.category_id).first()
            post_dict['category_name'] = category.name
            post_dict['category_id'] = category.id
        else:
            post_dict['category_name'] = ''
            post_dict['category_id'] = ''

        return post_dict


class Images(BaseModel, db.Model):
    """帖子 图片"""
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    url = db.Column(db.String(256), nullable=False)


class Comment(BaseModel, db.Model):
    """评论/回复表"""
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))  # 父评论id
    parent = db.relationship('Comment', remote_side=[id])  # 自关联
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    # images = db.relationship('Images', backref='comment')

    def to_dict(self):
        base = {
            'comment_id': self.id,
            'user_id': self.id,
            'post_id': self.post_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'parent_comment': self.parent.to_dict(),
            'like_count': self.like_count
        }
        return base


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


class Notification(db.Model):
    """消息推送"""
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('cm_user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)
