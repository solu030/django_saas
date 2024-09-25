import datetime
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from web import models
from django_saas.settings import WHITE_REGEX_URL_LIST

class Tracer():
    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None
        self.wiki = None
class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.tracer = Tracer()
        user_id = request.session.get('user_id',0)
        user_obj = models.UserInfo.objects.filter(id=user_id).first()
        request.tracer.user = user_obj
        if request.path_info in WHITE_REGEX_URL_LIST:
            return
        if not request.tracer.user:
            return redirect("login")
        trans_obj = models.Transaction.objects.filter(user=request.tracer.user,status=2).order_by('-id').first()
        current_datetime = datetime.datetime.now()
        if trans_obj.end_datetime and trans_obj.end_datetime < current_datetime:
            trans_obj = models.Transaction.objects.filter(user=request.tracer.user,status=2,price_policy__category=1).first()
        request.tracer.price_policy = trans_obj.price_policy

    def process_view(self,request,view,args,kwargs):
        project_id = kwargs.get('project_id')
        # if not project_id:
        #     return
        if not request.path_info.startswith("/manage/"):
            return
        my_obj = models.Project.objects.filter(creator=request.tracer.user,id=project_id).first()
        if my_obj:
            request.tracer.project = my_obj
            wiki_id = request.GET.get('wiki_id')
            if wiki_id and wiki_id.isdecimal():
                wiki_obj = models.Wiki.objects.filter(id=wiki_id, project=request.tracer.project).first()
                if wiki_obj:
                    request.tracer.wiki = wiki_obj
            return
        join_obj = models.ProjectUser.objects.filter(user=request.tracer.user,project_id=project_id).first()
        if join_obj:
            request.tracer.project = join_obj.project
            wiki_id = request.GET.get('wiki_id')
            if wiki_id and wiki_id.isdecimal():
                wiki_obj = models.Wiki.objects.filter(id=wiki_id, project=request.tracer.project).first()
                if wiki_obj:
                    request.tracer.wiki = wiki_obj
            return
        return redirect('project_list')