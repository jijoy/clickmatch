from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Index(models.Model):
    user = models.ForeignKey(User)
    index = models.IntegerField(default=1)
    total = models.IntegerField(default=0)