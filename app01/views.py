from django.core.validators import RegexValidator
from django.shortcuts import render,redirect
from django import forms

from app01 import models
# Create your views here.
def send_sms(request):
    pass

class RegisterModelForm(forms.ModelForm):
    password = forms.CharField(label="密码",widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="确认密码",widget=forms.PasswordInput)
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



def register(request):
    form = RegisterModelForm()

    return render(request,'app01/register.html',{'form':form})