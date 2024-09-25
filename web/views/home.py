import json
import datetime

from django.shortcuts import render,redirect
from django.http import JsonResponse,HttpResponse
from django_redis import get_redis_connection
from urllib.parse import parse_qs

from utils.encrypt import uid
from utils.AliPay import AliPay
from web import models

def index(request):
    return render(request,"index.html")

def price(request):
    price_list = models.PricePolicy.objects.filter(category=2)
    return render(request,"price.html",{"price_list":price_list})

def price_payment(request,policy_id):
    number = request.GET.get("number","")
    policy_object = models.PricePolicy.objects.filter(id=policy_id,category=2).first()
    if not policy_object:
        return redirect("price")
    if not number or not number.isdecimal():
        return redirect("price")
    number = int(number)
    if number < 1:
        return redirect("price")
    total_price = number * policy_object.price
    trans_object = models.Transaction.objects.filter(user=request.tracer.user,status=2).order_by("-id").first()
    balance = 0
    #如果当前还有vip
    if request.tracer.price_policy.category == 2:
        total_datetime = trans_object.start_datetime - trans_object.end_datetime
        balance_datetime = trans_object.end_datetime - datetime.datetime.now()
        if total_datetime.days == balance_datetime.days:
            balance = trans_object.price / total_datetime.days * (balance_datetime.days - 1)
        else:
            balance = trans_object.price / total_datetime.days * balance_datetime.days
    if balance > total_price:
        return redirect("price")
    context = {
        "policy_object_id": policy_object.id,
        "total_price": total_price,
        "pay_price": total_price - round(balance,2),
        "number": number,
        "balance": round(balance,2),
    }
    conn = get_redis_connection()
    key = "payment_{}".format(request.tracer.user.mobile_phone)
    conn.set(key, json.dumps(context), nx=60 * 30)
    context["policy_object"] = policy_object
    context["trans_object"] = trans_object
    return render(request,"payment.html",context)

def pay(request):
    conn = get_redis_connection()
    context_string = conn.get("payment_{}".format(request.tracer.user.mobile_phone))
    if not context_string:
        return redirect("price")
    context = json.loads(context_string.decode("utf-8"))
    order_id = uid(request.tracer.user.mobile_phone)
    pay_price = context["pay_price"]
    price_policy = models.PricePolicy.objects.filter(id=context["policy_object_id"]).first()
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy= price_policy,
        count=context["number"],
        price=context["pay_price"],
    )
    ali_pay = AliPay()
    #api参数
    pay_url = ali_pay.direct_pay(
        subject="tracer套餐升级",
        out_trade_no=order_id,
        total_amount=pay_price,
    )
    return redirect(pay_url)

def pay_notify(request):
    ali_pay = AliPay()
    if request.method == "GET":
        params = request.GET.dict()
        sign = params.pop("sign",None)
        status = ali_pay.verify(params,sign)
        if status:
            return HttpResponse("支付成功")
        return HttpResponse("支付失败")
    else:
        #没有公网ip，api无法访问接口
        body_string = request.body.decode("utf-8")
        post_data = parse_qs(body_string)
        post_dict = {}
        for k,v in post_data.items():
            post_dict[k] = v[0]
        sign = post_dict.pop("sign",None)
        status = ali_pay.verify(post_dict,sign)
        if status:
            current_datetime = datetime.datetime.now()
            #取订单号
            out_trade_no = post_dict["out_trade_no"]
            trans_object = models.Transaction.objects.filter(order=out_trade_no).first()
            trans_object.status = 2
            trans_object.create_datetime = current_datetime
            trans_object.end_datetime = current_datetime + datetime.timedelta(days=365 * trans_object.count)
            trans_object.save()
            return HttpResponse("success")
        return HttpResponse("error")