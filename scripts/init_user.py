import django_env
from web import models

models.UserInfo.objects.create(
    username='solu',
    email='21156489@qq.com',
    mobile_phone='13165489752',
    password='12345678'
)
