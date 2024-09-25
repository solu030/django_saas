from django.contrib import admin
from django.urls import path,re_path,include
from web.views import account,home,project,statistics,wiki,file,setting,issues,dashboard

urlpatterns = [
    path('register/',account.register,name='register'),
    path('send/sms/',account.send_Sms,name='send_Sms'),
    path('login/',account.login,name='login'),
    path('get/img/',account.img_code,name='img_code'),
    path('login/sms/',account.login_Sms,name='login_Sms'),
    path('index/',home.index,name='index'),
    path('logot/', account.logout, name='logout'),

    path('price/', home.price, name='price'),
    re_path(r'^price/payment/(?P<policy_id>\d+)/$', home.price_payment, name='price_payment'),
    path('pay/', home.pay, name='pay'),
    path('pay/notify/', home.pay_notify, name='pay_notify'),

    path('project/list/',project.project_list,name='project_list'),
    re_path(r'^project/star/(?P<project_type>\w+)/(?P<project_id>\d+)/$',project.project_star,name='project_star'),
    re_path(r'^project/unstar/(?P<project_type>\w+)/(?P<project_id>\d+)/$',project.project_unstar,name='project_unstar'),
    re_path(r'^manage/(?P<project_id>\d+)/',include([
        re_path(r'^dashboard/$',dashboard.dashboard,name='dashboard'),
        re_path(r'^dashboard/issues/charts/$', dashboard.issues_charts, name='issues_charts'),

        re_path(r'^issues/$',issues.issues,name='issues'),
        re_path(r'^issues/detail/(?P<issues_id>\d+)/$', issues.issues_detail, name='issues_detail'),
        re_path(r'^issues/record/(?P<issues_id>\d+)/$', issues.issues_record, name='issues_record'),
        re_path(r'^issues/change/(?P<issues_id>\d+)/$', issues.issues_change, name='issues_change'),
        re_path(r'^issues/invite/$', issues.issues_invite, name='issues_invite'),

        re_path(r'^statistics/$',statistics.statistics,name='statistics'),
        re_path(r'^statistics/priority/charts/$',statistics.priority_charts,name='priority_charts'),
        re_path(r'^statistics/charts/$',statistics.statistics_charts,name='statistics_charts'),


        re_path(r'^file/$',file.file_list,name='file'),
        re_path(r'^file/delete/$',file.file_delete,name='file_delete'),
        re_path(r'^file/save/$', file.file_save, name='file_save'),
        re_path(r'^cos/credential/$',file.cos_credential,name='cos_credential'),
        re_path(r'^file/download/(?P<file_id>\d+)/$', file.file_download, name='file_download'),

        re_path(r'^wiki/$',wiki.wiki,name='wiki'),
        re_path(r'^wiki/add/$', wiki.wiki_add, name='wiki_add'),
        re_path(r'^wiki/update/$', wiki.wiki_update, name='wiki_update'),
        re_path(r'^wiki/delete/$', wiki.wiki_delete, name='wiki_delete'),
        re_path(r'^wiki/catalog/$', wiki.wiki_catalog, name='wiki_catalog'),
        re_path(r'^wiki/upload/$', wiki.wiki_upload, name='wiki_upload'),

        re_path(r'^setting/$',setting.setting,name='setting'),
        re_path(r'^setting/delete/$', setting.setting_delete, name='setting_delete'),
    ],None)),
    re_path(r'^invite/join/(?P<code>\w+)/$', issues.issues_join, name='issues_join'),
]