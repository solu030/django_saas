import random

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django_redis import get_redis_connection
from django import forms


from web import models
from django_saas.settings import TEMPLATES_SMSID
from utils.encrypt import md5
from web.forms.bootstrap import BootstrapForm
# Create your views here.

class RegisterModelForm(forms.ModelForm):
    password = forms.CharField(
        label="密码",
        min_length=8,
        max_length=16,
        error_messages={
            "min_length": "密码长度必须大于8",
            "max_length": "密码长度必须小于16"
        },
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        label="确认密码",
        min_length=8,
        max_length=16,
        error_messages={
            "min_length": "密码长度必须大于8",
            "max_length": "密码长度必须小于16"
        },
        widget=forms.PasswordInput
    )
    code = forms.CharField(label="验证码",max_length=4)
    mobile_phone = forms.CharField(
        label="手机号",
        validators=[RegexValidator(r'^1[358]\d{9}$|^147\d{8}$|^176\d{8}$',"手机号格式错误")]
    )
    class Meta:
        model = models.UserInfo
        fields = ['username','password','confirm_password','email','mobile_phone','code']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name,field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = "请输入{}".format(field.label)

    def clean_username(self):
        username = self.cleaned_data['username']
        exists = models.UserInfo.objects.filter(username=username).exists()
        if exists:
            raise ValidationError("用户名已存在")
        return username
    def clean_email(self):
        email = self.cleaned_data['email']
        exists = models.UserInfo.objects.filter(email=email).exists()
        if exists:
            raise ValidationError("邮箱已注册")
        return email
    def clean_password(self):
        password = self.cleaned_data['password']
        pwd = md5(password)
        return pwd
    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = md5(self.cleaned_data['confirm_password'])
        if password != confirm_password:
            raise ValidationError("密码不一致")
        return confirm_password
    def clean_mobile_phone(self):
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if exists:
            raise ValidationError("手机号已注册")
        return mobile_phone
    def clean_code(self):
        code = self.cleaned_data['code']
        try:
            mobile_phone = self.cleaned_data['mobile_phone']
        except KeyError:
            raise ValidationError("请输入手机号")
        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError("请发送验证码")
        redis_code = redis_code.decode("utf-8")
        if code.strip() != redis_code:
            raise ValidationError("验证码错误")
        return code

class SmsForm(forms.Form):
    tpl = forms.CharField(max_length=12)
    mobile_phone = forms.CharField(
        max_length=11,
        validators=[RegexValidator(r'^1[358]\d{9}$|^147\d{8}$|^176\d{8}$',"手机号格式错误")]
    )
    def clean_tpl(self):
        tpl = self.cleaned_data['tpl']
        tid = TEMPLATES_SMSID.get(tpl)
        if not tid:
            raise ValidationError("非法模板")
        return tpl
    def clean_mobile_phone(self):
        tpl = self.cleaned_data.get('tpl')
        mobile_phone = self.cleaned_data['mobile_phone']
        exist = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if tpl == "register":
            if exist:
                raise ValidationError("手机号已注册")
        elif tpl == "login":
            if not exist:
                raise ValidationError("请注册后登录")

        code = random.randrange(1000,9999)
        #发送短信 没有sdk 先伪造
        print(code)
        conn = get_redis_connection()
        conn.set(mobile_phone,code,ex=60)
        return mobile_phone

class LoginForm(BootstrapForm):
    username = forms.CharField(max_length=32,label="用户名邮箱或手机号")
    password = forms.CharField(max_length=32,label="密码",widget=forms.PasswordInput)
    code = forms.CharField(max_length=5,label="验证码")

    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.request = request

    def clean_password(self):
        pwd = self.cleaned_data['password']
        pwd = md5(pwd)
        return pwd
    def clean_code(self):
        code = self.cleaned_data['code']
        if not code:
            raise ValidationError("请输入验证码")
        try:
            se_code = self.request.session["img_code"]
        except:
            raise ValidationError("验证码已过期")
        if se_code.strip().upper() != code.strip().upper():
            raise ValidationError("验证码错误")
        return code


class LoginSmsForm(BootstrapForm):
    username = forms.CharField(max_length=32,label="用户名")
    mobile_phone = forms.CharField(
        max_length=11,
        label="手机号",
        validators=[RegexValidator(r'^1[358]\d{9}$|^147\d{8}$|^176\d{8}$',"手机号格式错误")]
    )
    code = forms.CharField(max_length=4,label="验证码")

    def clean_username(self):
        username = self.cleaned_data['username']
        exists = models.UserInfo.objects.filter(username=username).exists()
        if not exists:
            raise ValidationError("用户名错误")
        #return到cleaned_data["username"]
        return username
    def clean_mobile_phone(self):
        username = self.cleaned_data.get("username")
        mobile_phone = self.cleaned_data['mobile_phone']
        exists = models.UserInfo.objects.filter(mobile_phone=mobile_phone).exists()
        if not exists:
            raise ValidationError("手机号未注册")
        exists = models.UserInfo.objects.filter(username=username,mobile_phone=mobile_phone).exists()
        if not exists:
            raise ValidationError("请输入对应用户的手机号")
        return mobile_phone
    def clean_code(self):
        mobile_phone = self.cleaned_data.get('mobile_phone')
        #发完短信后清空手机号触发
        if not mobile_phone:
            raise ValidationError("请输入手机号")
        code = self.cleaned_data['code']
        conn = get_redis_connection()
        redis_code = conn.get(mobile_phone)
        if not redis_code:
            raise ValidationError("验证码过期或未发送")
        redis_code = redis_code.decode("utf-8")
        if code.strip() != redis_code:
            raise ValidationError("验证码错误")
        return code