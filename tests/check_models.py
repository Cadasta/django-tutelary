from tutelary.decorators import permissioned_model
from django.db import models


@permissioned_model
class CheckModel1(models.Model):
    name = models.CharField(max_length=100)

    class TutelaryMeta:
        perm_type = 'check'
        path_fields = ('name',)
        actions = [('check.list', {'permissions_object': None}),
                   ('check.create', {'permissions_object': None}),
                   ('check.detail',
                    {'error_message': 'detail view not allowed'}),
                   'check.delete']

    def __str__(self):
        return self.name


class CheckModel2(models.Model):
    name = models.CharField(max_length=100)
    container = models.ForeignKey(CheckModel1)

    def __str__(self):
        return self.name


permissioned_model(
    CheckModel2, perm_type='check2',
    path_fields=('container', 'pk'),
    actions=[('check2.list', {'permissions_object': 'container'}),
             ('check2.create', {'permissions_object': 'container'}),
             'check2.detail',
             'check2.delete']
)


class CheckModel3(models.Model):
    name = models.CharField(max_length=100)
    container = models.ForeignKey(CheckModel1)

    def __str__(self):
        return self.name


@permissioned_model
class CheckModel4(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class TutelaryMeta:
        perm_type = 'check4'
        path_fields = ('name',)
        actions = [('check4.list', {'permissions_object': None}),
                   ('check4.create', {'permissions_object': None}),
                   'check4.detail',
                   'check4.delete']


@permissioned_model
class CheckModel5(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class TutelaryMeta:
        perm_type = 'check5'
        path_fields = ('name',)
        actions = ['check5.detail', 'check5.delete']


class CheckModel1Broken(models.Model):
    name = models.CharField(max_length=100)

    class TutelaryMeta:
        perm_type = 'check'
        path_fields = ('name',)
        actions = [('check.list', {'permissions_object': None}),
                   ('check.create', {'permissions_object': None}),
                   ('check.detail',
                    {'error_message': 'detail view not allowed'}),
                   'check.delete']

    def __str__(self):
        return self.name
