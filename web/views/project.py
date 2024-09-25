import time

from django.shortcuts import render,redirect
from django.http import JsonResponse

from web.forms.project import ProjectModelForm
from web import models
from utils.cos import create_bucket


def project_list(request):
    if request.method == 'GET':
        projects_dict = {"star":[],"my":[],"join":[]}
        my_project_list = models.Project.objects.filter(creator=request.tracer.user)
        for item in my_project_list:
            if item.star:
                projects_dict["star"].append({"value":item,"type":"my"})
            else:
                projects_dict["my"].append(item)
        join_project_list = models.ProjectUser.objects.filter(user=request.tracer.user)
        for item in join_project_list:
            if item.star:
                projects_dict["star"].append({"value":item.project,"type":"join"})
            else:
                projects_dict["join"].append(item.project)
        form = ProjectModelForm(request)
        return render(request,"project_list.html",{"form":form,"project_dict":projects_dict})
    form = ProjectModelForm(request,data=request.POST)
    if form.is_valid():
        bucket = "{}-{}-1309792818".format(request.tracer.user.mobile_phone,str(int(time.time())))
        region = 'ap-chengdu'
        create_bucket(bucket,region)
        form.instance.bucket = bucket
        form.instance.region = region
        form.instance.creator = request.tracer.user
        instance = form.save()

        issues_type_list = []
        for item in models.IssuesType.INIT_ISSUES_TYPE:
            issues_type_list.append(models.IssuesType(project=instance, title=item))
        models.IssuesType.objects.bulk_create(issues_type_list)

        return JsonResponse({'status':True})
    return JsonResponse({'status':False,"error":form.errors})

def project_star(request,project_type,project_id):
    if project_type == "my":
        models.Project.objects.filter(creator=request.tracer.user,id=project_id).update(star=True)
    elif project_type == "join":
        models.ProjectUser.objects.filter(user=request.tracer.user,id=project_id).update(star=True)
    return redirect("project_list")

def project_unstar(request,project_type,project_id):
    print(project_type)
    if project_type == "my":
        models.Project.objects.filter(creator=request.tracer.user,id=project_id).update(star=False)
    elif project_type == "join":
        models.ProjectUser.objects.filter(user=request.tracer.user,id=project_id).update(star=False)
    return redirect("project_list")