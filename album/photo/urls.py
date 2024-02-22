from django.urls import path
from photo.views import home, upload, oss_home

# App名称
# 用于Django幕后的url查询
app_name = 'photo'

# url列表
urlpatterns = [
    path('', oss_home, name='oss_home'),
    path('upload/', upload, name='upload'),
#    path('oss-home/', oss_home, name='oss_home'),
]