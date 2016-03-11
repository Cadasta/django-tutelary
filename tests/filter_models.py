from django.db import models
from tutelary.decorators import permissioned_model


@permissioned_model
class Org(models.Model):
    name = models.CharField(max_length=100)

    class TutelaryMeta:
        perm_type = 'org'
        path_fields = ('name',)
        actions = [('org.list', {'permissions_object': None})]


@permissioned_model
class Proj(models.Model):
    name = models.CharField(max_length=100)
    org = models.ForeignKey(Org)

    class TutelaryMeta:
        perm_type = 'proj'
        path_fields = ('org', 'name',)
        actions = [('proj.list', {'permissions_object': 'org'}),
                   'proj.detail',
                   'proj.delete']
