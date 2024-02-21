import time

import requests
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
import oss2

from photo.models import Photo

# 填入阿里云账号的 <AccessKey ID> 和 <AccessKey Secret>
auth = oss2.Auth('LTAI5t6rbyq4dYMwdniSuiDG', 'plrlzuIoDeJk7FxP5BqzyLoQPHH6fV')
# 填入 OSS 的 <域名> 和 <Bucket名>
bucket = oss2.Bucket(auth, 'oss-cn-hangzhou.aliyuncs.com', 'vaporemix-photo-album')


# Create your views here.

class ObjIterator(oss2.ObjectIteratorV2):
    # 初始化
    def __init__(self, bucket):
        super().__init__(bucket)
        self.fetch_with_retry()

    # 分页要求实现__len__
    def __len__(self):
        return len(self.entries)

    # 分页要求实现__getitem__
    def __getitem__(self, key):
        return self.entries[key]

    # 此方法从云端抓取文件数据
    # 然后将数据赋值给 self.entries
    def _fetch(self):
        result = self.bucket.list_objects_v2(prefix=self.prefix,
                                             delimiter=self.delimiter,
                                             continuation_token=self.next_marker,
                                             start_after=self.start_after,
                                             fetch_owner=self.fetch_owner,
                                             encoding_type=self.encoding_type,
                                             max_keys=self.max_keys,
                                             headers=self.headers)
        self.entries = result.object_list + [oss2.models.SimplifiedObjectInfo(prefix, None, None, None, None, None)
                                             for prefix in result.prefix_list]
        # 让图片以上传时间倒序
        self.entries.sort(key=lambda obj: -obj.last_modified)

        return result.is_truncated, result.next_continuation_token


def oss_home(request):
    photos = ObjIterator(bucket)
    # for photo in photos:
    #     print(photo.etag)
    #     print(photo.__dict__)
    #     print(photo.key)
    paginator = Paginator(photos, 6)
    page_number = request.GET.get('page')
    paged_photos = paginator.get_page(page_number)
    context = {'photos': paged_photos}
    # 处理登入登出的POST请求
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        # 登入
        if user is not None and user.is_superuser:
            login(request, user)
        # 登出
        isLogout = request.POST.get('isLogout')
        if isLogout == 'True':
            logout(request)
    return render(request, 'photo/oss_list.html', context)


def home(request):
    # 处理登入登出的POST请求
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        # 登入
        if user is not None and user.is_superuser:
            login(request, user)
        # 登出
        isLogout = request.POST.get('isLogout')
        if isLogout == 'True':
            logout(request)

    # photos = Photo.objects.all()
    photos = Photo.objects.filter(author_id=request.user.id)
    # 新增分页代码
    paginator = Paginator(photos, 5)
    page_number = request.GET.get('page')
    paged_photos = paginator.get_page(page_number)
    # 将分页器对象传入上下文
    context = {'photos': paged_photos}



    return render(request, 'photo/list.html', context)


def put_object_oss(ObjectName, LocalFile, BucketName):
    # 上传文件名，本地文件路径
    bucket.put_object(ObjectName, LocalFile)
    # 返回的网址
    return f"https://{BucketName}.oss-cn-hangzhou.aliyuncs.com/{ObjectName}"


def upload(request):
    if request.method == 'POST' and request.user.is_superuser:
        data = request.POST
        for i, j in zip(request.FILES.getlist('images'), data.getlist('story')):
            print(i, j)
            photo = Photo(image=i)
            photo.introduction = j
            photo.author = User.objects.get(id=request.user.id)
            photo.save()

    return redirect('home')

# def upload(request):
#     if request.method == 'POST' and request.user.is_superuser:
#         print(request.POST.get('story'))
#         images = request.FILES.getlist('images')
#         for i in images:
#             # image_object = request.FILES.get('InMemoryUploadedFile')
#
#             # 重命名（获取上传文件的后缀名）
#             ext = i.name.rsplit('.')[-1]
#             # 重新命名的名字（我这里使用time，防止重复的可以选择uuid）
#             key = "{}.{}".format(time.strftime("%Y%m%d%H%M%S"), ext)
#
#             # read()获取image_object的bytes字节串；
#             # image_object_bytes = i.read()
#             # put_object_oss(ObjectName=key, LocalFile=image_object_bytes, BucketName='vaporemix-photo-album')
#
#             photo = Photo(image=i)
#             photo.author = User.objects.get(id=request.user.id)
#             photo.image_name = Photo(image=i)
#             photo.save()
#
#     return redirect('home')
