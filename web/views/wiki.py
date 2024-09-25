from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from web.forms.wiki import WikiModelForm
from web import models
from utils.cos import upload_file
from utils.encrypt import uid
def wiki(request,project_id):
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'wiki.html')
    wiki_obj = models.Wiki.objects.filter(id=wiki_id,project=request.tracer.project).first()
    if not wiki_obj:
        return render(request, 'wiki.html')
    return render(request,'wiki.html',{'wiki_obj':wiki_obj})

def wiki_add(request,project_id):
    if request.method == 'GET':
        form = WikiModelForm(request)
        return render(request, 'wiki_add.html',{'form':form})
    form = WikiModelForm(request,data=request.POST)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()
        url = reverse('wiki',kwargs={'project_id':project_id})
        return redirect(url)
    return render(request, 'wiki_add.html', {'form':form})

def wiki_update(request,project_id):
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'wiki.html')
    wiki_obj = models.Wiki.objects.filter(id=wiki_id,project=request.tracer.project).first()
    if not wiki_obj:
        return render(request, 'wiki.html')
    if request.method == 'GET':
        form = WikiModelForm(request,instance=wiki_obj)
        return render(request, 'wiki_add.html', {'form': form})
    form = WikiModelForm(request, data=request.POST,instance=wiki_obj)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.save()
        url = reverse('wiki',kwargs={'project_id':project_id})
        detail_url = f'{url}?wiki_id={wiki_id}'
        return redirect(detail_url)
    return render(request, 'wiki_add.html', {'form': form})

def wiki_delete(request,project_id):
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'wiki.html')
    models.Wiki.objects.filter(id=wiki_id,project=request.tracer.project).delete()
    return render(request, 'wiki.html')

def wiki_catalog(request,project_id):
    data = models.Wiki.objects.filter(project=request.tracer.project).values("id","title","parent_id").order_by("depth","id")
    return JsonResponse({"status":True,"data":list(data)})

@csrf_exempt
@xframe_options_exempt
def wiki_upload(request,project_id):
    result = {
        "success":0,
        "message":None,
        "url":None,
    }
    img_obj = request.FILES.get('editormd-image-file')
    if not img_obj:
        result["message"] = "文件上传失败，请重试"
        return JsonResponse(result)
    ext = img_obj.name.rsplit('.')[-1]
    key = "{}.{}".format(uid(request.tracer.user.mobile_phone),ext)
    image_url = upload_file(
        bucket=request.tracer.project.bucket,
        region=request.tracer.project.region,
        file_object=img_obj,
        key=key
    )
    result["url"] = image_url
    result["success"] = 1
    return JsonResponse(result)