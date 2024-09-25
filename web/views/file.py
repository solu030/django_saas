import json
import requests
from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from web.forms.file import FileModelForm,UploadFileModelForm
from utils.cos import delete_file,delete_file_list,credential
from web import models

def file_list(request,project_id):
    folder_id = request.GET.get('folder_id',"")
    parent_obj = None
    if folder_id.isdecimal():
        parent_obj = models.FileRepository.objects.filter(project=request.tracer.project,id=int(folder_id),file_type=2).first()
    if request.method == 'GET':
        queryset = models.FileRepository.objects.filter(project=request.tracer.project,)
        if parent_obj:
            folder_list = queryset.filter(parent=parent_obj).order_by('-file_type')
        else:
            folder_list = queryset.filter(parent__isnull=True).order_by('-file_type')
        breadcrumb_list = []
        parent = parent_obj
        while parent:
            breadcrumb_list.insert(0, {"id":parent.id,"name":parent.name})
            parent = parent.parent
        form = FileModelForm(request,parent_obj)
        context = {
            "form": form,
            "folder_list": folder_list,
            "breadcrumb_list": breadcrumb_list,
            "folder_object": parent_obj
        }
        return render(request,"file.html",context)
    fid = request.POST.get('fid','')
    folder_object = None
    if fid.isdecimal():
        folder_object = models.FileRepository.objects.filter(project=request.tracer.project,id=int(fid),file_type=2).first()
    if folder_object:
        form = FileModelForm(request,parent_obj,data=request.POST,instance=folder_object)
    else:
        form = FileModelForm(request,parent_obj,data=request.POST)
    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.update_user = request.tracer.user
        form.instance.parent = parent_obj
        form.instance.file_type = 2
        form.save()
        return JsonResponse({'status':True})
    return JsonResponse({'status':False,"error":form.errors})

def file_delete(request,project_id):
    fid = request.GET.get('fid')
    obj = models.FileRepository.objects.filter(project=request.tracer.project,id=int(fid)).first()
    if not obj:
        return JsonResponse({'status':False})
    if obj.file_type==1:
        request.tracer.project.use_space -= obj.file_size
        request.tracer.project.save()
        delete_file(request.tracer.project.bucket,request.tracer.project.region,obj.key)
        obj.delete()
        return JsonResponse({'status': True})
    total_size = 0
    folder_list = [obj,]
    key_list = []
    for item in folder_list:
        child_list = models.FileRepository.objects.filter(project=request.tracer.project,parent=item).order_by('-file_type')
        for child in child_list:
            if child.file_type == 2:
                folder_list.append(child)
            else:
                total_size += child.file_size
                key_list.append({"Key":child.key})
    if key_list:
        delete_file_list(request.tracer.project.bucket,request.tracer.project.region,key_list)
    if total_size:
        request.tracer.project.use_space -= total_size
        request.tracer.project.save()
    obj.delete()
    return JsonResponse({'status':True})

@csrf_exempt
def cos_credential(request,project_id):
    per_file_limit = request.tracer.price_policy.per_file_size * 1024 * 1024
    total_size = 0
    valid_space = (request.tracer.price_policy.project_space - request.tracer.project.use_space) * 1024 * 1024
    file_list = json.loads(request.body.decode('utf-8'))
    for item in file_list:
        if item["fileSize"] > per_file_limit:
            return JsonResponse({'status':False,"error":"单文件大小超出限制,请升级套餐"})
        total_size += item["fileSize"]
    if total_size > valid_space:
        return JsonResponse({'status':False,"error":"项目可用空间不足,请升级套餐"})
    #空间校验通过再生成临时凭证
    data_dict = credential(request.tracer.project.bucket,request.tracer.project.region)
    return JsonResponse({'status':True,"data":data_dict})

@csrf_exempt
def file_save(request, project_id):
    form = UploadFileModelForm(request,data=request.POST)
    if form.is_valid():
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict.update({"project": request.tracer.project, "file_type": 1, "update_user": request.tracer.user})
        instance = models.FileRepository.objects.create(**data_dict)
        #use_space存储单位为MB,dashboard展示单位为B,pricepolicy总容量单位为GB，待整合
        request.tracer.project.use_space += (data_dict["file_size"] / 1024 / 1024)
        request.tracer.project.save()
        result = {
            "id": instance.id,
            "name": instance.name,
            "file_size": instance.file_size,
            "username": instance.update_user.username,
            "datetime": instance.update_datetime.strftime("%Y年%m月%d日 %H:%M"),
            "file_path": instance.file_path,
            #reverse把url转换成路由 /manage/3/file/download/29/
            "download_url": reverse("file_download",kwargs={"project_id":project_id,"file_id":instance.id}),
        }
        return JsonResponse({'status': True, "data": result})
    return JsonResponse({'status': False, "data": "存储失败"})

def file_download(request, project_id, file_id):
    """ 中文文件下载会乱码 """
    file_obj = models.FileRepository.objects.filter(project=request.tracer.project,id=file_id).first()
    res = requests.get(file_obj.file_path)
    data = res.content
    response = HttpResponse(data)
    response['Content-Disposition'] = "attachment; filename={}".format(file_obj.name)
    return response
