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
        actions = {
            'org.list':   {'description': "Can list existing organisations"},
            'org.create': {'description': "Can create organisations"},
            'org.delete': {'description': "Can delete organisations"}
        }

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
        actions = {
            'project.list':   {'description': "Can list existing projects"},
            'project.create': {'description': "Can create projects"},
            'project.delete': {'description': "Can delete projects"}
        }

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
        actions = {
            'party.list':   {'description': "Can list existing parties"},
            'party.detail': {'description': "Can view details of a party"},
            'party.create': {'description': "Can create parties",
                             'allowed_methods': ['GET']},
            'party.edit':   {'description': "Can update existing parties",
                             'allowed_methods': ['GET']},
            'party.delete': {'description': "Can delete parties",
                             'allowed_methods': ['GET']}
        }

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
        actions = {
            'parcel.list':   {'description': "Can list existing parcels"},
            'parcel.detail': {'description': "Can view details of a parcel"},
            'parcel.create': {'description': "Can create parcels",
                              'allowed_methods': ['GET']},
            'parcel.edit':   {'description': "Can update existing parcels",
                              'allowed_methods': ['GET']},
            'parcel.delete': {'description': "Can delete parcels",
                              'allowed_methods': ['GET']}
        }

    def get_absolute_url(self):
        return reverse('parcel-detail', kwargs={'pk': self.pk})


permissioned_model(
    Policy, perm_type='policy', path_fields=['name'],
    actions={
        'policy.list':   {'description': "Can list existing policies"},
        'policy.detail': {'description': "Can view details of a policy"},
        'policy.create': {'description': "Can create policies"},
        'policy.edit':   {'description': "Can update existing policies"},
        'policy.delete': {'description': "Can delete policies"}
    }
)
permissioned_model(
    User, perm_type='user', path_fields=['username'],
    actions={
        'user.list':   {'description': "Can list existing users"},
        'user.detail': {'description': "Can view details of a user"},
        'user.create': {'description': "Can create users"},
        'user.edit':   {'description': "Can update existing users"},
        'user.delete': {'description': "Can delete users"}
    }
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
