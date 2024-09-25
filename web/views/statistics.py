from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count
from web import models
def statistics(request,project_id):
    return render(request,'statistics.html')

def priority_charts(request,project_id):
    start = request.GET.get('start')
    end = request.GET.get('end')
    data_dict = {}
    #前端所需格式[name,count]
    for k,v in models.Issues.priority_choices:
        data_dict[k] = [v,0]
    result = models.Issues.objects.filter(project_id=project_id,create_datetime__gte=start,
                                          create_datetime__lte=end).values("priority").annotate(ct=Count('id'))
    for item in result:
        data_dict[item["priority"]][1] = item["ct"]
    return JsonResponse({"status": True, "data": list(data_dict.values())})

def statistics_charts(request,project_id):
    start = request.GET.get('start')
    end = request.GET.get('end')
    #这个图展示的是指派者的问题，无指派者则归为none
    all_user_dict = {}
    all_user_dict[request.tracer.project.creator_id] = {
        "name": request.tracer.project.creator.username,
        "status": {item[0]: 0 for item in models.Issues.status_choices}
    }
    all_user_dict[None] = {
        "name": "未指派",
        "status": {item[0]: 0 for item in models.Issues.status_choices}
    }
    user_list = models.ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            "name": item.user.username,
            "status": {item[0]: 0 for item in models.Issues.status_choices}
        }
    issues = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start, create_datetime__lte=end)
    for item in issues:
        if not item.assign:
            all_user_dict[None]["status"][item.status] += 1
        else:
            all_user_dict[item.assign_id]["status"][item.status] += 1
    categories = [data["name"] for data in all_user_dict.values()]
    data_result_dict = {}
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {
            "name": item[1],
            "data": []
        }
    for k,v in models.Issues.status_choices:
        for row in all_user_dict.values():
            count = row["status"][k]
            data_result_dict[k]["data"].append(count)
    context = {
        "status": True,
        "data": {
            "categories": categories,
            "series": list(data_result_dict.values())
        }
    }
    return JsonResponse(context)