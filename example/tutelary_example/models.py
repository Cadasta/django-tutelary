from django.core.urlresolvers import reverse
from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    status = models.CharField(max_length=40)

    class Meta:
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})


class Parcel(models.Model):
    address = models.CharField(max_length=200)
    status = models.CharField(max_length=40)

    class Meta:
        ordering = ['status', 'address']

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})
