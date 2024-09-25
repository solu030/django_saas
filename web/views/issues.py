import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from web.forms.issues import IssuesModelForm,IssuesRecordModelForm,IssuesInviteModelForm
from utils.Pagination import Pagination
from utils.encrypt import uid
from web import models

class CheckFilter(object):
    def __init__(self, request,name,data_list):
        self.request = request
        self.name = name
        self.data_list = data_list
    def __iter__(self):
        for k,v in self.data_list:
            ck = ""
            value_list = self.request.GET.getlist(self.name)
            #关键是要理解生成器生成的是前端 下次 点击的url,所以带参数请求时生成的url要不带参数
            if str(k) in value_list:
                ck = "checked"
                #生成的url点击不带该参数，故再次点击取消checked并取消该参数
                value_list.remove(str(k))
            else:
                #生成的url/manage/6/issues/?priority=success点击会带有参数
                value_list.append(str(k))
            query_dict = self.request.GET.copy()
            query_dict.mutable = True
            query_dict.setlist(self.name,value_list)
            if "page" in query_dict:
                query_dict.pop("page")
            url = "{}?{}".format(self.request.path_info,query_dict.urlencode())
            tpl = '<a class="cell" href="{url}"><input type="checkbox" {ck}/><label>{v}</label></a>'
            html = tpl.format(ck=ck,v=v,url=url)
            yield mark_safe(html)

class SelectFilter(object):
    def __init__(self, request,name,data_list):
        self.request = request
        self.name = name
        self.data_list = data_list

    def __iter__(self):
        yield mark_safe("<select class='select2' style='width:100%;' multiple='multiple'>")
        value_list = self.request.GET.getlist(self.name)
        for k,v in self.data_list:
            selected = ""
            if str(k) in value_list:
                selected = "selected"
                value_list.remove(str(k))
            else:
                value_list.append(str(k))
            query_dict = self.request.GET.copy()
            query_dict.mutable = True
            query_dict.setlist(self.name, value_list)
            if "page" in query_dict:
                query_dict.pop("page")
            url = "{}?{}".format(self.request.path_info, query_dict.urlencode())
            html = "<option value={url} {selected}>{text}</option>".format(url=url,selected=selected,text=v)
            yield mark_safe(html)
        yield mark_safe("</select>")
def issues(request,project_id):
    if request.method == "GET":
        #根据query_params筛选数据库中的数据，进而展示不同的数据，实现搜索的目的
        allow_filter_list = ["status", "issues_type", "priority", "assign", "attention"]
        condition = {}
        for name in allow_filter_list:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condition["{}__in".format(name)] = value_list

        form = IssuesModelForm(request)
        queryset = models.Issues.objects.filter(project_id=project_id).filter(**condition)
        page_obj = Pagination(request,queryset,page_size=1)
        page_obj.html()
        project_issues_type = tuple(models.IssuesType.objects.filter(project_id=project_id).values_list("id","title"))
        total_project_user = [(request.tracer.project.creator_id, request.tracer.project.creator.username)]
        join_user = models.ProjectUser.objects.filter(project_id=project_id).values_list("user_id","user__username")
        total_project_user.extend(join_user)
        invite_form = IssuesInviteModelForm()
        context = {
            "form": form,
            "issues_list": page_obj.page_queryset,
            "page_string": page_obj.page_string,
            "invite_form": invite_form,
            "filter_list": [
                {"title": "问题类型", "filter": CheckFilter(request,"issues_type",project_issues_type)},
                {"title": "状态", "filter": CheckFilter(request,"status",models.Issues.status_choices)},
                {"title": "优先级", "filter": CheckFilter(request, "priority", models.Issues.priority_choices)},
                {"title": "指派者", "filter": SelectFilter(request, "assign", total_project_user)},
                {"title": "关注者", "filter": SelectFilter(request, "attention", total_project_user)},
            ]
        }
        return render(request, 'issues.html', context)
    form = IssuesModelForm(request,data=request.POST)
    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.save()
        return JsonResponse({'status':True})
    return JsonResponse({'status':False,"error":form.errors})

def issues_detail(request,project_id,issues_id):
    if request.method == "GET":
        issues_object = models.Issues.objects.filter(project_id=project_id,id=issues_id).first()
        form = IssuesModelForm(request,instance=issues_object)
        return render(request,"issues_detail.html",{"form":form,"issues_object":issues_object})

@csrf_exempt
def issues_record(request,project_id,issues_id):
    if request.method == "GET":
        data_list = []
        issues_reply = models.IssuesReply.objects.filter(issues__project=request.tracer.project.id, issues_id=issues_id)
        for row in issues_reply:
            data = {
                'id': row.id,
                'reply_type_text': row.get_reply_type_display(),
                'content': row.content,
                'creator': row.creator.username,
                'datetime': row.create_datetime.strftime('%Y-%m-%d %H:%M'),
                'parent_id': row.reply_id,
            }
            data_list.append(data)
        return JsonResponse({'status':True,"data":data_list})
    form = IssuesRecordModelForm(data=request.POST)
    if form.is_valid():
        form.instance.issues_id = issues_id
        form.instance.reply_type = 2
        form.instance.creator = request.tracer.user
        instance = form.save()
        info = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime('%Y-%m-%d %H:%M'),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status':True,"data":info})
    return JsonResponse({'status':False,"error":form.errors})

@csrf_exempt
def issues_change(request,project_id,issues_id):
    post_dict = json.loads(request.body.decode('utf-8'))
    name = post_dict.get("name")
    value = post_dict.get("value")
    #修改指派时会莫名发两次请求
    if not name:
        return JsonResponse({'status':False})
    issues_object = models.Issues.objects.filter(project=request.tracer.project,id=issues_id).first()
    filed_object = models.Issues._meta.get_field(name)
    if name in ["subject", "desc", "start_date", "end_date", ]:
        if not value:
            if not filed_object.null:
                return JsonResponse({'status':False,"error":"此选项不能为空!"})
            setattr(issues_object,name,None)
            issues_object.save()
            change_record = "将{}设置为空".format(filed_object.verbose_name)
        else:
            setattr(issues_object,name,value)
            issues_object.save()
            change_record = "将{}设置为{}".format(filed_object.verbose_name,value)
        instance = models.IssuesReply.objects.create(
            reply_type = 1,
            issues = issues_object,
            content = change_record,
            creator = request.tracer.user,
        )
        reply_dict = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime('%Y-%m-%d %H:%M'),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status':True,"data":reply_dict})

    if name in ["issues_type", "module", "assign", "parent", ]:
        if not value:
            if not filed_object.null:
                return JsonResponse({'status':False,"error":"此选项不能为空!"})
            setattr(issues_object,name,None)
            issues_object.save()
            change_record = "将{}设置为空".format(filed_object.verbose_name)
        else:
            #UserInfo没有project外键
            if name == "assign":
                if value == str(request.tracer.project.creator_id):
                    assign_object = request.tracer.project.creator
                else:
                    project_object = models.ProjectUser.objects.filter(project_id=project_id,user_id=value).first()
                    if project_object:
                        assign_object = project_object.user
                    else:
                        assign_object = None
                #不判断用户类型也能实现指派
                # assign_object = filed_object.remote_field.model.objects.filter(id=value).first()
                if not assign_object:
                    return JsonResponse({'status':False,"error":"选项不存在!"})
                setattr(issues_object,name,assign_object)
                issues_object.save()
                change_record = "将{}修改为{}".format(filed_object.verbose_name,str(assign_object))
            else:
                fore_object = filed_object.remote_field.model.objects.filter(id=value,project_id=project_id).first()
                if not fore_object:
                    return JsonResponse({'status':False,"error":"选项不存在!"})
                setattr(issues_object,name,fore_object)
                issues_object.save()
                change_record = "将{}设置为{}".format(filed_object.verbose_name,str(fore_object))
        instance = models.IssuesReply.objects.create(
            reply_type = 1,
            issues = issues_object,
            content = change_record,
            creator = request.tracer.user,
        )
        reply_dict = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime('%Y-%m-%d %H:%M'),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status':True,"data":reply_dict})

    if name in ["priority", "status", "mode", ]:
        selected_text = None
        for k,v in filed_object.choices:
            if str(k) == value:
                selected_text = v
        if not selected_text:
            return JsonResponse({'status':False,"error":"请选择正确的选项"})
        setattr(issues_object,name,value)
        issues_object.save()
        change_record = "将{}修改为{}".format(filed_object.verbose_name,selected_text)
        instance = models.IssuesReply.objects.create(
            reply_type = 1,
            issues = issues_object,
            content = change_record,
            creator = request.tracer.user,
        )
        reply_dict = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime('%Y-%m-%d %H:%M'),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status':True,"data":reply_dict})

    if name in ["attention", ]:
        if not isinstance(value,list):
            return JsonResponse({'status':False,"error":"数据格式错误"})
        if not value:
            issues_object.attention.set(value)
            issues_object.save()
            change_record = "将{}设置为空".format(filed_object.verbose_name)
        else:
            user_dict = {str(request.tracer.project.creator_id):request.tracer.project.creator.username}
            project_user_list = models.ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_list:
                user_dict[str(item.user_id)] = item.user_username
            username_list = []
            for user_id in value:
                if user_id not in user_dict:
                    return JsonResponse({'status':False,"error":"所选用户不存在，请重试"})
                username_list.append(user_dict[user_id])
            issues_object.attention.set(value)
            change_record = "将{}修改为{}".format(filed_object.verbose_name,",".join(username_list))
        instance = models.IssuesReply.objects.create(
            reply_type = 1,
            issues = issues_object,
            content = change_record,
            creator = request.tracer.user,
        )
        reply_dict = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime('%Y-%m-%d %H:%M'),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status':True,"data":reply_dict})



    return JsonResponse({'status':False})
@csrf_exempt
def issues_invite(request,project_id):
    form = IssuesInviteModelForm(data=request.POST)
    if form.is_valid():
        if request.tracer.user != request.tracer.project.creator:
            form.add_error("period", "只有创建者才能生成邀请码!")
            return JsonResponse({'status':False,"error":form.errors})
        invite_code = uid(request.tracer.user.mobile_phone)
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.instance.code = invite_code
        form.save()
        url = "{scheme}://{host}{path}".format(
            scheme=request.scheme,
            host=request.get_host(),
            path=reverse("issues_join",kwargs={"code": invite_code})
        )
        return JsonResponse({'status':True,"data":url})
    return JsonResponse({'status':False,"error":form.errors})

def issues_join(request,code):
    invite_object = models.ProjectInvite.objects.filter(code=code).first()
    current_datetime = datetime.datetime.now()
    if not invite_object:
        return render(request,"invite_join.html",{"error":"邀请码错误"})
    if request.tracer.user == invite_object.creator:
        return render(request,"invite_join.html",{"error":"创建者无需再加入项目"})
    exists = models.ProjectUser.objects.filter(user=request.tracer.user).exists()
    if exists:
        return render(request,"invite_join.html",{"error":"已加入项目"})
    #项目的套餐为创建者的套餐
    trans_object = models.Transaction.objects.filter(user=request.tracer.project.creator).order_by("-id").first()
    free_object = models.PricePolicy.objects.filter(category=1).first()
    if trans_object.price_policy.category == 1:
        max_member = free_object.project_member
    else:
        if trans_object.end_datetime < current_datetime:
            max_member = free_object.project_member
        else:
            max_member = trans_object.price_policy.project_member
    current_member = models.ProjectUser.objects.filter(project=invite_object.project).count() + 1
    if current_member >= max_member:
        return render(request,"invite_join.html",{"error":"项目成员已满，请升级套餐"})

    limit_datetime = invite_object.create_datetime + datetime.timedelta(minutes=invite_object.period)
    if current_datetime > limit_datetime:
        return render(request,"invite_join.html",{"error":"邀请码已过期，请重新申请"})
    if invite_object.count:
        if invite_object.use_count >= invite_object.count:
            return render(request,"invite_join.html",{"error":"邀请数量已满，请重新申请邀请码"})
        invite_object.use_count += 1
        invite_object.save()
    invite_object.project.join_count += 1
    invite_object.save()
    models.ProjectUser.objects.create(user=request.tracer.user, project=invite_object.project)
    return render(request,"invite_join.html",{"project": invite_object.project})



