from django.core.exceptions import ValidationError
from django import forms
from web.forms.bootstrap import BootstrapModelForm
from web import models
from utils.cos import check_file

class FileModelForm(BootstrapModelForm):
    class Meta:
        model = models.FileRepository
        fields = ["name"]

    def __init__(self,request,parent_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_obj = parent_obj

    def clean_name(self):
        name = self.cleaned_data["name"]
        queryset = models.FileRepository.objects.filter(project=self.request.tracer.project, name=name,file_type=2)
        if self.parent_obj:
            exists = queryset.filter(parent=self.parent_obj).exists()
        else:
            exists = queryset.filter(parent__isnull=True).exists()
        if exists:
            raise ValidationError("文件夹已存在")
        return name

class UploadFileModelForm(BootstrapModelForm):
    etag = forms.CharField(label="cosETag")
    class Meta:
        model = models.FileRepository
        exclude = ["project", "file_type", "update_user", "update_datetime"]
    def __init__(self,request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_file_path(self):
        file_path = self.cleaned_data["file_path"]
        return "https://{}".format(file_path)

    # def clean(self):
    #     key = self.cleaned_data.get("key")
    #     etag = self.cleaned_data.get("etag")
    #     size = self.cleaned_data.get("size")
    #     if not key or not etag:
    #         return self.cleaned_data
    #
    #     from qcloud_cos.cos_exception import CosException
    #     try:
    #         result = check_file(self.request.tracer.project.bucket,self.request.tracer.project.region,key)
    #     except CosException as e:
    #         self.add_error("key", "文件不存在")
    #         return self.cleaned_data
    #     cos_etag = result.get("ETag")
    #     if cos_etag != etag:
    #         self.add_error("etag","ETag错误")
    #     cos_length = result.get("Content-Length")
    #     if int(cos_length) != size:
    #         self.add_error("file_size","文件大小错误")
    #     return self.cleaned_data

