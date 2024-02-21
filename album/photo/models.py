from django.contrib.auth.models import User
from django.db import models

from PIL import Image
from django.utils.timezone import now


# Create your models here.
class Photo(models.Model):
    image = models.ImageField(upload_to='photo/%Y%m%d/')
    image_name = models.CharField(max_length=100,verbose_name='img-name')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(default=now)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.image_name
