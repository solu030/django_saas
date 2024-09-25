from django import forms

from web.forms.bootstrap import BootstrapModelForm
from web import models

class IssuesModelForm(BootstrapModelForm):
    class Meta:
        model = models.Issues
        exclude = ['project', 'creator', 'create_datetime', 'last_update_datetime']
        widgets = {
            "assign": forms.Select(attrs={'class': 'selectpicker'}),
            "attention": forms.SelectMultiple(attrs={'class': 'selectpicker'}),
        }

    def __init__(self,request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        issueType_choices = models.IssuesType.objects.filter(project=request.tracer.project).values_list('id', "title")
        self.fields['issues_type'].choices = issueType_choices

        module_choices = [("","暂不选择模块")]
        module_list = models.Issues.objects.filter(project=request.tracer.project).values_list('id', "module")
        for module in module_list:
            if not None in module:
                module_choices.extend(module)
        self.fields['module'].choices = module_choices

        user_choices = [(request.tracer.project.creator.id, request.tracer.project.creator.username)]
        join_list = models.ProjectUser.objects.filter(project=request.tracer.project).values_list('user_id', "user__username")
        user_choices.extend(join_list)
        #extend无返回值 [("","暂不指定指派")].extend(user_choices)取返回值none
        self.fields['assign'].choices = [("","暂不指定指派")] + user_choices
        self.fields['attention'].choices = user_choices

        parent_choices = [("","暂不选择父问题")]
        parent_list = models.Issues.objects.filter(project=request.tracer.project).values_list('id', "subject")
        parent_choices.extend(parent_list)
        self.fields['parent'].choices = parent_choices

class IssuesRecordModelForm(BootstrapModelForm):
    class Meta:
        model = models.IssuesReply
        fields = ["content","reply"]

class IssuesInviteModelForm(BootstrapModelForm):
    class Meta:
        model = models.ProjectInvite
        fields = ["period","count"]

