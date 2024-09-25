import time
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from web import models
def dashboard(request,project_id):
    status_dict = {}
    #key为status序号,value为{text,count}
    for key,text in models.Issues.status_choices:
        status_dict[key] = {"text":text,"count":0}
    issues_data = models.Issues.objects.filter(project_id=project_id).values("status").annotate(count=Count("id"))
    for item in issues_data:
        status_dict[item["status"]]["count"] = item["count"]
    user_list = models.ProjectUser.objects.filter(project_id=project_id).values("user_id","user__username")
    top_10 = models.Issues.objects.filter(project_id=project_id,assign__isnull=False).order_by("-id")[0:10]

    context = {
        "status_dict": status_dict,
        "user_list": user_list,
        "top_ten_object": top_10,
    }
    return render(request, 'dashboard.html',context)

def issues_charts(request,project_id):
    today = datetime.datetime.now().date()
    date_dict = {}
    for i in range(0,30):
        date = today - datetime.timedelta(days=i)
        #{date:[时间戳,count]}
        date_dict[date.strftime("%Y-%m-%d")] = [time.mktime(date.timetuple()) * 1000, 0]
    #annotate按ctime取count
    result = models.Issues.objects.filter(project_id=project_id,create_datetime__gte=today-datetime.timedelta(days=30)).extra(
        select={"ctime": "strftime('%%Y-%%m-%%d', web_issues.create_datetime)"}).values('ctime').annotate(ct=Count("id"))
    for item in result:
        #将ct赋值给dict
        date_dict[item["ctime"]][1] = item["ct"]
    return JsonResponse({"status": True,"data": list(date_dict.values())})
