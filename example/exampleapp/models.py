from django.core.urlresolvers import reverse
from django.db import models
from django.contrib.auth.models import User
from tutelary.base import Action
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
        actions = (('org.list', "Can list existing organisations"),
                   ('org.create', "Can create organisations"),
                   ('org.delete', "Can delete organisations"))

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
        actions = (('project.list', "Can list existing projects"),
                   ('project.create', "Can create projects"),
                   ('project.delete', "Can delete projects"))

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
        actions = (('party.list', "Can list existing parties"),
                   ('party.view', "Can view details of a party"),
                   ('party.create', "Can create parties", ['GET']),
                   ('party.edit', "Can update existing parties", ['GET']),
                   ('party.delete', "Can delete parties", ['GET']))

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
        actions = (('parcel.list', "Can list existing parcels"),
                   ('parcel.view', "Can view details of a parcel"),
                   ('parcel.create', "Can create parcels", ['GET']),
                   ('parcel.edit', "Can update existing parcels", ['GET']),
                   ('parcel.delete', "Can delete parcels", ['GET']))

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


permissioned_model(Policy, perm_type='policy', path_fields=['name'],
                   actions=(('policy.list', "Can list existing policies"),
                            ('policy.view', "Can view details of a policy"),
                            ('policy.create', "Can create policies"),
                            ('policy.edit', "Can update existing policies"),
                            ('policy.delete', "Can delete policies")))
permissioned_model(User, perm_type='user', path_fields=['username'],
                   actions=(('user.list', "Can list existing users"),
                            ('user.view', "Can view details of a user"),
                            ('user.create', "Can create users"),
                            ('user.edit', "Can update existing users"),
                            ('user.delete', "Can delete users")))

Action.register('statistics')
