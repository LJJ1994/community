__author__ = 'LJJ'
__date__ = '2019/9/19 上午10:10'

import random

# 用户默认昵称
USER_DEFAULT_NICK_NAME = "笨笨猪" + str(random.randint(1, 99999))

# 用户默认地址
USER_DEFAULT_LOCATION = "火星"


# 短信验证码有效期,单位为秒
SMS_CODE_REDIS_EXPIRES = 5*60

# 该时间内不能再发送手机验证码
SEND_SMS_CODE_REDIS_EXPIRES = 60

# 登录错误尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误限制的时间，单位为秒
LOGIN_ERROR_FORBID_TIME = 10*60

# 七牛域名
QINIU_URL_DOMAIN = "http://ptu2ehw5u.bkt.clouddn.com/"

# 城区缓存时间, 单位为秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页展示最多的房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据的Redis缓存时间，单位：秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页展示的评论最大数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面数据Redis缓存时间，单位：秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋列表页面每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋列表页面页数缓存时间，单位为秒
HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

# 支付宝支付网关地址
ALIPAY_URL_GATEWAY = "https://openapi.alipaydev.com/gateway.do?"
