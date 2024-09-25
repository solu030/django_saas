from web import models
from web.forms.bootstrap import BootstrapForm,BootstrapModelForm

class WikiModelForm(BootstrapModelForm):
    class Meta:
        model = models.Wiki
        fields = ["title","content","parent"]

    def __init__(self,request,*args, **kwargs):
        #bug:可以选择自己为自己的父文章,因为找不到父文章，所以在目录上不会渲染 修改方法:传入wiki_id去除自己 通过中间件封装wiki成功修改
        super().__init__(*args, **kwargs)
        total_data_list = [("","请选择文章")]
        data_list = models.Wiki.objects.filter(project=request.tracer.project).values_list("id","title")
        total_data_list.extend(data_list)
        #编辑时才需要去除自己
        if request.tracer.wiki is not None:
            total_data_list.remove((request.tracer.wiki.id,request.tracer.wiki.title))
        self.fields["parent"].choices = total_data_list
