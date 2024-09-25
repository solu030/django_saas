from django import forms
from django.core.exceptions import ValidationError
from web.forms.bootstrap import BootstrapModelForm
from web import models
from web.forms.widgets import ColorRadioSelect

class ProjectModelForm(BootstrapModelForm):
    bootstrap_exclude_field = ["color",]
    class Meta:
        model = models.Project
        fields = ['name','color','desc']
        widgets = {
            'desc': forms.Textarea(),
            "color": ColorRadioSelect(attrs={'class':'color-radio'}),
        }

    def __init__(self, request,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request


    def clean_name(self):
        name = self.cleaned_data['name']
        exists = models.Project.objects.filter(name=name,creator=self.request.tracer.user).exists()
        if exists:
            raise ValidationError("项目名已存在")
        current_count = models.Project.objects.filter(creator=self.request.tracer.user).count()
        if self.request.tracer.price_policy.project_num <= current_count:
            raise ValidationError("项目数达到上限，请升级套餐")
        return name
