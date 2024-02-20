from django.db import models
from PIL import Image
from django.utils.timezone import now


# Create your models here.
class Photo(models.Model):
    image = models.ImageField(upload_to='photo/%Y%m%d/')
    created = models.DateTimeField(default=now)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.image.name
