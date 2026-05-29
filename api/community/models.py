import uuid

from django.db import models

class Post(models.Model):
    title = models.TextField()
    body = models.TextField()

