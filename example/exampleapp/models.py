from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from tutelary.models import Policy
from tutelary.decorators import permissioned_model


@permissioned_model
class Organisation(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)
        permissions = (('org.create', "Can create organisations"),
                       ('org.delete', "Can delete organisations"))

    class TutelaryMeta:
        perm_type = 'organisation'
        path_fields = ('name',)

    def __str__(self):
        return self.name


@permissioned_model
class Project(models.Model):
    name = models.CharField(max_length=100)
    organisation = models.ForeignKey(Organisation)

    class Meta:
        ordering = ('organisation', 'name')
        permissions = (('project.create', "Can create projects"),
                       ('project.delete', "Can delete projects"))

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organisation', 'name')

    def __str__(self):
        return self.name


@permissioned_model
class Party(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('project', 'name')
        permissions = (('party.list', "Can list existing parties"),
                       ('party.view', "Can view details of a party"),
                       ('party.create', "Can create parties"),
                       ('party.edit', "Can update existing parties"),
                       ('party.delete', "Can delete parties"))

    class TutelaryMeta:
        perm_type = 'party'
        path_fields = ('project', 'pk')

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})


@permissioned_model
class Parcel(models.Model):
    project = models.ForeignKey(Project)
    address = models.CharField(max_length=200)

    class Meta:
        ordering = ('project', 'address')
        permissions = (('parcel.list', "Can list existing parcels"),
                       ('parcel.view', "Can view details of a parcel"),
                       ('parcel.create', "Can create parcels"),
                       ('parcel.edit', "Can update existing parcels"),
                       ('parcel.delete', "Can delete parcels"))

    class TutelaryMeta:
        perm_type = 'parcel'
        path_fields = ('project', 'pk')

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})


class UserPolicyAssignment(models.Model):
    user = models.ForeignKey(User)
    policy = models.ForeignKey(Policy)
    organisation = models.ForeignKey(Organisation, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, blank=True)
    index = models.IntegerField()

    class Meta:
        ordering = ('index',)


permissioned_model(Policy, 'policy', ['name'])
permissioned_model(User, 'user', ['username'])
