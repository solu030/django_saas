from django.template import Library
from django.urls import reverse
from web import models

register = Library()
@register.inclusion_tag("inclusion/all_project_list.html")
def all_project_list(request):
    my = models.Project.objects.filter(creator=request.tracer.user)
    join = models.ProjectUser.objects.filter(user=request.tracer.user)
    return ({"my": my, "join": join,"request": request})

@register.inclusion_tag("inclusion/manage_menu_list.html")
def manage_menu_list(request):
    data_list = [
        {"url": reverse("dashboard",kwargs={"project_id":request.tracer.project.id}) ,"title":'概述'},
        {"url": reverse("issues", kwargs={"project_id": request.tracer.project.id}), "title": '问题'},
        {"url": reverse("statistics", kwargs={"project_id": request.tracer.project.id}), "title": '统计'},
        {"url": reverse("file", kwargs={"project_id": request.tracer.project.id}), "title": '文件'},
        {"url": reverse("wiki", kwargs={"project_id": request.tracer.project.id}), "title": 'wiki'},
        {"url": reverse("setting", kwargs={"project_id": request.tracer.project.id}), "title": '设置'},
    ]
    for item in data_list:
        if request.path_info == item["url"]:
            item["class"] = "active"
    return ({"data_list":data_list})
