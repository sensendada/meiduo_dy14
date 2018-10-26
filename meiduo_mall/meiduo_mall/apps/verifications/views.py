import random
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response

from rest_framework.views import APIView
from meiduo_mall.libs.yuntongxun.sms import CCP
from verifications import constants


# 获取日志器
import logging
logging = logging.getLogger('django')


# GET /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(APIView):
    def get(self, request, mobile):
        """
        获取短信验证码
        1.随机生成6位数作为短信验证码内容
        2.在redis中保存短信验证码内容, 以'mobile'为key, 以'验证码内容'为 value
        3.使用云通讯给mobile发送短信
        4.返回应答, 发送成功
        :param request:
        :param mobile:
        :return:
        """

        # 判断60s之内是否给mobile发送短信
        redis_conn = get_redis_connection('verify_codes')
        send_flag = redis_conn.get('send_flag_%s' % mobile)

        if send_flag:
            return Response({'message': '发送短信过于频繁'}, status=status.HTTP_400_BAD_REQUEST)
            # 1.随机生成6位数字作为短信验证码内容
        sms_code = '%06d' % random.randint(0, 999999)
        # 2.在redis中保存短信验证码内容, 以'mobile'为key,以验证码内容为value
        # redis管道: 可以向redis管道中添加多个redis命令.然后一次性执行
        # 创建redis管道对象
        pl = redis_conn.pipeline()
        # 向redis管道中盘哪个添加所有命令
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存给mobile发送短信标记
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 一次性执行管道中所有的命令
        pl.execute()

        # 3. 使用云通讯给moblie发送短信
        expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        # try:
        #     res = CCP().send_template_sms(mobile, [sms_code, expires], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logging.error(e)
        #     return Response({'message': '发送短信异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        #
        # if res != 0:
        #     return Response({'message': '发送短信失败'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response('发送短信成功')


