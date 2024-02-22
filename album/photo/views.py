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
        self.entries = result.object_list + [SimplifiedOssObjectInfo(prefix, None, None, None, None, None)
                                             for prefix in result.prefix_list]
        # 让图片以上传时间倒序
        self.entries.sort(key=lambda obj: -obj.last_modified)

        return result.is_truncated, result.next_continuation_token


class SimplifiedOssObjectInfo(oss2.models.SimplifiedObjectInfo):
    def __init__(self, key, last_modified, etag, type, size, storage_class):
        #: 文件名，或公共前缀名。
        super().__init__(key, last_modified, etag, type, size, storage_class)
        self.key = key

        #: 文件的最后修改时间
        self.last_modified = last_modified

        #: HTTP ETag
        self.etag = etag

        #: 文件类型
        self.type = type

        #: 文件大小
        self.size = size

        #: 文件的存储类别，是一个字符串。
        self.storage_class = storage_class

        #: owner信息, 类型为: class:`Owner <oss2.models.Owner>`
        self.owner = self.owner

        # meta data
        self.meta = None


def oss_home(request):
    photos = ObjIterator(bucket)
    paginator = Paginator(photos, 6)
    page_number = request.GET.get('page')
    paged_photos = paginator.get_page(page_number)
    for i in paged_photos:
        i.meta = bucket.get_object(i.key).headers
        if 'X-Oss-Meta-Author' not in i.meta:
            i.meta['X_Oss_Meta_Author'] = ''
        else:
            i.meta['X_Oss_Meta_Author'] = i.meta['X-Oss-Meta-Author']
        if 'X-Oss-Meta-Story' not in i.meta:
            i.meta['X_Oss_Meta_Story'] = ''
        else:
            i.meta['X_Oss_Meta_Story'] = i.meta['X-Oss-Meta-Story']

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


def put_object_oss(ObjectName, LocalFile, BucketName, meta: dict):
    headers = {
        'x-oss-meta-author': meta["author"],
        'x-oss-meta-story': meta["story"],
        'Content-Type': 'application/json; charset=utf-8'
    }
    print("元数据：", headers)
    # 上传文件名，本地文件路径
    bucket.put_object(key=ObjectName, data=LocalFile, headers=headers)
    # 返回的网址
    return f"https://{BucketName}.oss-cn-hangzhou.aliyuncs.com/{ObjectName}"


def upload(request):
    if request.method == 'POST' and request.user.is_superuser:
        data = request.POST
        for i, j in zip(request.FILES.getlist('images'), data.getlist('story')):
            # 重命名（获取上传文件的后缀名）
            ext = i.name.rsplit('.')[-1]
            # 重新命名的名字（我这里使用time，防止重复的可以选择uuid）
            key = "{}.{}".format(time.strftime("%Y%m%d%H%M%S"), ext)
            # meta data
            meta = {
                'author': str(User.objects.get(id=request.user.id)),
                'story': j
            }

            image_object_bytes = i.read()
            put_object_oss(ObjectName=key, LocalFile=image_object_bytes, BucketName='vaporemix-photo-album',
                           meta=meta)
            #
            # photo = Photo(image=i)
            # photo.introduction = j
            # photo.author = User.objects.get(id=request.user.id)
            # photo.save()

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
