__author__ = 'LJJ'
__date__ = '2019/9/27 上午11:55'

from qiniu import Auth, etag, put_data
import qiniu.config


# 需要填写你的 Access Key 和 Secret Key
access_key = 'DKBwZ3jYFmRUitplgBTkvgvZS5tel4h6HBtZHhHX'
secret_key = 'U0FurqXznNUX7lvF_vpLoN8hxhh7qPOp0-OZnTx_'


# 构建一个存储的函数
def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)

    # 要上传的空间
    bucket_name = 'communities'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 上传文件的信息
    ret, info = put_data(token, None, file_data)
    # print(info)
    # print("*"*10)
    # print(ret)
    if info.status_code == 200:
        # 上传成功,返回文件名
        return ret.get("key")
    else:
        # 上传失败
        raise Exception("上传失败")


if __name__ == "__main__":
    with open("./faker.jpeg", "rb") as f:
        file_data = f.read()
        storage(file_data)
