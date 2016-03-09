from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from tutelary.engine import Action
from tutelary.models import Policy
from tutelary.decorators import permissioned_model


@permissioned_model
class Organisation(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'organisation'
        path_fields = ('name',)
        actions = [
            ('organisation.list',   {'permissions_object': None}),
            ('organisation.create', {'permissions_object': None}),
            'organisation.delete'
        ]

    def __str__(self):
        return self.name


@permissioned_model
class Project(models.Model):
    name = models.CharField(max_length=100)
    organisation = models.ForeignKey(Organisation)

    class Meta:
        ordering = ('organisation', 'name')

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organisation', 'name')
        actions = [
            ('project.list', {'permissions_object': 'organisation'}),
            ('project.create', {'permissions_object': 'organisation'}),
            'project.delete'
        ]

    def __str__(self):
        return self.name


@permissioned_model
class Party(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('project', 'name')

    class TutelaryMeta:
        perm_type = 'party'
        path_fields = ('project', 'pk')
        actions = [
            ('party.list',   {'description': "List existing parties",
                              'permissions_object': 'project'}),
            ('party.create', {'description': "Create parties",
                              'permissions_object': 'project'}),
            ('party.detail', {'description': "View details of a party"}),
            ('party.edit',   {'description': "Update existing parties"}),
            ('party.delete', {'description': "Delete parties"})
        ]

    def get_absolute_url(self):
        return reverse('party-detail', kwargs={'pk': self.pk})


@permissioned_model
class Parcel(models.Model):
    project = models.ForeignKey(Project)
    address = models.CharField(max_length=200)

    class Meta:
        ordering = ('project', 'address')

    class TutelaryMeta:
        perm_type = 'parcel'
        path_fields = ('project', 'pk')
        actions = [
            ('parcel.list',   {'description': "List existing parcels",
                               'permissions_object': 'project'}),
            ('parcel.create', {'description': "Create parcels",
                               'permissions_object': 'project'}),
            ('parcel.detail', {'description': "View details of a parcel"}),
            ('parcel.edit',   {'description': "Update existing parcels"}),
            ('parcel.delete', {'description': "Delete parcels"})
        ]

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})


permissioned_model(
    Policy, perm_type='policy', path_fields=['name'],
    actions=[
        ('policy.list', {'description': "Can list existing policies",
                         'permissions_object': None}),
        ('policy.create', {'description': "Can create policies",
                           'permissions_object': None}),
        ('policy.detail', {'description': "Can view details of a policy"}),
        ('policy.edit',   {'description': "Can update existing policies"}),
        ('policy.delete', {'description': "Can delete policies"})
    ]
)
permissioned_model(
    User, perm_type='user', path_fields=['username'],
    actions=[
        ('user.list',   {'permissions_object': None}),
        ('user.create', {'permissions_object': None}),
        'user.detail',
        'user.edit',
        'user.delete'
    ]
)

Action.register('statistics')


class UserPolicyAssignment(models.Model):
    user = models.ForeignKey(User)
    policy = models.ForeignKey(Policy)
    organisation = models.ForeignKey(Organisation, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, blank=True)
    index = models.IntegerField()

    class Meta:
        ordering = ('index',)


def set_user_policies(user):
    def do_one(pol_assign):
        vs = dict(
            organisation=(pol_assign.organisation.name
                          if pol_assign.organisation else None),
            project=(pol_assign.project.name
                     if pol_assign.project else None),
        )
        pol = Policy.objects.get(name=pol_assign.policy)
        return (pol, vs) if vs else pol
    pols = [do_one(pa)
            for pa in UserPolicyAssignment.objects.filter(user=user)]
    user.assign_policies(*pols)
