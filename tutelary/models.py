from django.db import models


class Policy(models.Model):
    name = models.CharField(max_length=200)
    body = models.TextField()
