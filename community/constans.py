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
QINIU_DOMIN_PREFIX = "http://pyh16juz1.bkt.clouddn.com/"

# 用户默认头像
USER_DEFAULT_AVATAR = "FmLpSj_f58frfukhsTuB-1Mr6hwO"

# 支付宝支付网关地址
ALIPAY_URL_GATEWAY = "https://openapi.alipaydev.com/gateway.do?"
