import uuid
import datetime

from django.shortcuts import render,HttpResponse,redirect
from django.http import JsonResponse
from django.db.models import Q
from io import BytesIO

from web.forms.account import RegisterModelForm,SmsForm,LoginSmsForm,LoginForm
from utils.img_code import check_code
from web import models

def register(request):
    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html',{'form':form})
    form = RegisterModelForm(request.POST)
    if form.is_valid():
        price_policy = models.PricePolicy.objects.filter(category=1,title="个人免费版").first()
        instance = form.save()
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user=instance,
            price_policy=price_policy,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now(),
        )
        return JsonResponse({'status':True,"data":"/login/"})
    return JsonResponse({"status": False,"error": form.errors})

def login(request):
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request,"login.html",{'form':form})
    form = LoginForm(request,request.POST)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user_obj = models.UserInfo.objects.filter(
            Q(username=username) |
            Q(email=username) |
            Q(mobile_phone=username)).filter(password=password).first()

        if user_obj:
            request.session['user_id'] = user_obj.id
            request.session.set_expiry(60 * 60 * 24 * 7)
            return redirect('/index/')
        form.add_error('username',"用户名或密码错误")
    return render(request,"login.html",{'form':form})

def login_Sms(request):
    if request.method == 'GET':
        form = LoginSmsForm()
        return render(request,"login_sms.html",{'form':form})
    form = LoginSmsForm(request.POST)
    if form.is_valid():
        mobile_phone = form.cleaned_data.get('mobile_phone')
        user_obj = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        request.session['user_id'] = user_obj.id
        request.session.set_expiry(60 * 60 * 24 * 7)
        return JsonResponse({'status':True,"data":"/index/"})
    return JsonResponse({"status": False,"error": form.errors})

def send_Sms(request):
    form = SmsForm(data=request.GET)
    if form.is_valid():
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})

def img_code(request):
    img_obj,code = check_code()
    stream = BytesIO()
    img_obj.save(stream, 'png')
    request.session['img_code'] = code
    request.session.set_expiry(60)
    return HttpResponse(stream.getvalue())

def logout(request):
    request.session.flush()
    return redirect('index')

