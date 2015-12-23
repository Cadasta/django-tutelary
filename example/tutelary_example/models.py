from django.core.urlresolvers import reverse
from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    status = models.CharField(max_length=40)

    class Meta:
        ordering = ('name',)
        permissions = (('party.list', "Can list existing parties"),
                       ('party.view', "Can view details of a party"),
                       ('party.create', "Can create parties"),
                       ('party.edit', "Can update existing parties"),
                       ('party.delete', "Can delete parties"))

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})


class Parcel(models.Model):
    address = models.CharField(max_length=200)
    status = models.CharField(max_length=40)

    class Meta:
        ordering = ('status', 'address')
        permissions = (('parcel.list', "Can list existing parcels"),
                       ('parcel.view', "Can view details of a parcel"),
                       ('parcel.create', "Can create parcels"),
                       ('parcel.edit', "Can update existing parcels"),
                       ('parcel.delete', "Can delete parcels"))

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})
