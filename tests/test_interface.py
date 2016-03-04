from tutelary.engine import Action
from tutelary.decorators import permissioned_model, permission_required
from tutelary.mixins import PermissionRequiredMixin
from tutelary.exceptions import PermissionObjectException, DecoratorException
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpResponse
from django.test import RequestFactory
import django.views.generic as generic
import django.views.generic.edit as edit
import pytest
from .factories import UserFactory, PolicyFactory
from .datadir import datadir  # noqa


@pytest.fixture(scope="function")  # noqa
def setup(datadir, db):
    user1 = UserFactory.create(username='user1')
    user2 = UserFactory.create(username='user2')

    PolicyFactory.set_directory(str(datadir))
    pol1 = PolicyFactory.create(name='pol1', file='policy-1.json')
    pol2 = PolicyFactory.create(name='pol2', file='policy-2.json')
    pol3 = PolicyFactory.create(name='pol3', file='policy-3.json')

    Action.register(['check.list', 'check.create',
                     'check.detail', 'check.delete'])

    user1.assign_policies(pol1, pol2)
    user2.assign_policies(pol1, pol3)

    return (user1, user2)


@permissioned_model
class CheckModel1(models.Model):
    name = models.CharField(max_length=100)

    class TutelaryMeta:
        perm_type = 'check'
        path_fields = ('name',)
        actions = [('check.list', {'permissions_object': None}),
                   ('check.create', {'permissions_object': None}),
                   'check.detail',
                   ('check.delete', {'get_allowed': True})]

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


class DummyRequest:
    def __init__(self, user, method='GET'):
        self.user = user
        self.method = method


class CheckViewBase(PermissionRequiredMixin, generic.DetailView):
    permission_required = 'check.detail'

    def __init__(self, obj, user):
        self.model = obj
        self.obj = obj
        self.request = DummyRequest(user)


class CheckView1(CheckViewBase):
    def get_object(self):
        return self.obj


class CheckView2(CheckViewBase):
    def get_queryset(self):
        return [self.obj]


def test_mixin_basic_obj_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok_obj = CheckModel1(name='not-secret')
    secret_obj = CheckModel1(name='secret')

    assert CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert CheckView1(ok_obj, user2).has_permission()
    assert CheckView1(secret_obj, user2).has_permission()


def test_mixin_basic_queryset_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok_obj = CheckModel1(name='not-secret')
    secret_obj = CheckModel1(name='secret')

    assert CheckView2(ok_obj, user1).has_permission()
    assert not CheckView2(secret_obj, user1).has_permission()
    assert CheckView2(ok_obj, user2).has_permission()
    assert CheckView2(secret_obj, user2).has_permission()


def test_view_exceptions_no_policies(datadir, setup):  # noqa
    other_user = UserFactory.create(username='other')
    ok_obj = CheckModel1(name='not-secret')
    assert not CheckView1(ok_obj, other_user).has_permission()


class Check2ViewBase(PermissionRequiredMixin, generic.ListView):
    permission_required = 'check2.list'

    def __init__(self, obj, user):
        self.model = obj
        self.obj = obj
        self.request = DummyRequest(user)


class Check2View1(Check2ViewBase):
    def get_object(self):
        return self.obj


class Check2View2(Check2ViewBase):
    def get_queryset(self):
        return [self.obj]


def test_mixin_fk_obj_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok_container = CheckModel1(name='not-secret')
    secret_container = CheckModel1(name='secret')
    ok_obj = CheckModel2(name='visible', container=ok_container)
    secret_obj = CheckModel2(name='not-visible', container=secret_container)

    assert Check2View1(ok_obj, user1).has_permission()
    assert not Check2View1(secret_obj, user1).has_permission()
    assert Check2View1(ok_obj, user2).has_permission()
    assert Check2View1(secret_obj, user2).has_permission()


def test_mixin_fk_queryset_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok_container = CheckModel1(name='not-secret')
    secret_container = CheckModel1(name='secret')
    ok_obj = CheckModel2(name='visible', container=ok_container)
    secret_obj = CheckModel2(name='not-visible', container=secret_container)

    assert Check2View2(ok_obj, user1).has_permission()
    assert not Check2View2(secret_obj, user1).has_permission()
    assert Check2View2(ok_obj, user2).has_permission()
    assert Check2View2(secret_obj, user2).has_permission()


class CheckModel3(models.Model):
    name = models.CharField(max_length=100)
    container = models.ForeignKey(CheckModel1)

    def __str__(self):
        return self.name


def test_permission_object_exceptions(datadir, setup):  # noqa
    with pytest.raises(PermissionObjectException):
        permissioned_model(
            CheckModel3, perm_type='check3',
            path_fields=('container', 'pk'),
            actions=[('check3.list', {'permissions_object': 'not-there'}),
                     ('check3.create', {'permissions_object': 'container'}),
                     'check3.detail',
                     'check3.delete']
        )

    with pytest.raises(PermissionObjectException):
        permissioned_model(
            CheckModel3, perm_type='check3',
            path_fields=('container', 'pk'),
            actions=[('check3.list', {'permissions_object': 'name'}),
                     ('check3.create', {'permissions_object': 'container'}),
                     'check3.detail',
                     'check3.delete']
        )

    with pytest.raises(DecoratorException):
        class Dummy(models.Model):
            pass
        permissioned_model(
            Dummy, perm_type='dummy',
            path_fields=('name',)
        )

    with pytest.raises(DecoratorException):
        class Dummy:
            pass
        permissioned_model(
            Dummy, perm_type='dummy',
            path_fields=('name',),
            actions=['dummy.list']
        )


class CheckGetAllowedView(PermissionRequiredMixin, edit.DeleteView):
    permission_required = 'check.delete'

    def __init__(self, obj, user, method):
        self.model = obj
        self.obj = obj
        self.request = DummyRequest(user, method)

    def get_object(self):
        return self.obj


def test_get_allowed(datadir, setup):  # noqa
    user1, user2 = setup
    obj = CheckModel1(name='not-secret')

    assert CheckGetAllowedView(obj, user1, 'GET').has_permission()
    assert CheckGetAllowedView(obj, user2, 'GET').has_permission()
    assert not CheckGetAllowedView(obj, user1, 'POST').has_permission()
    assert CheckGetAllowedView(obj, user2, 'POST').has_permission()


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


class Check4ListView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'check4.list'

    def __init__(self, obj, user):
        self.model = obj
        self.obj = obj
        self.request = DummyRequest(user)

    def get_object(self):
        return self.obj


class Check4CreateView(PermissionRequiredMixin, edit.CreateView):
    permission_required = 'check4.create'

    def __init__(self, obj, user):
        self.model = obj
        self.obj = obj
        self.request = DummyRequest(user)

    def get_object(self):
        return self.obj


def test_mixin_null_perms_obj(datadir, setup):  # noqa
    user1, user2 = setup
    obj = CheckModel4(name='visible')
    new_obj = CheckModel4(name='new-one')

    assert Check4ListView(obj, user1).has_permission()
    assert not Check4CreateView(obj, user1).has_permission()
    assert Check4ListView(obj, user2).has_permission()
    assert Check4CreateView(new_obj, user2).has_permission()


@permissioned_model
class CheckModel5(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class TutelaryMeta:
        perm_type = 'check5'
        path_fields = ('name',)
        actions = ['check4.detail', 'check4.delete']


class Check5DetailView(PermissionRequiredMixin, generic.DetailView):
    permission_required = 'check5.detail'

    def __init__(self, obj, user):
        self.model = obj
        self.obj = obj
        self.request = DummyRequest(user)

    def get_object(self):
        return self.obj


def test_mixin_no_permissions_object(datadir, setup):  # noqa
    user1, user2 = setup
    obj = CheckModel5(name='check')

    assert not Check5DetailView(obj, user1).has_permission()
    assert Check5DetailView(obj, user2).has_permission()


@permission_required('check.list')
def func_view_ok(request):
    return HttpResponse("<html><body>Dummy response.</body></html>")


@permission_required('check3.create', raise_exception=True)
def func_view_bad(request):
    return HttpResponse("<html><body>Dummy response.</body></html>")


def test_function_view(datadir, setup):  # noqa
    user1, user2 = setup

    request = RequestFactory().get('/check')
    request.user = user1
    assert (func_view_ok(request).content ==
            b'<html><body>Dummy response.</body></html>')
    with pytest.raises(PermissionDenied):
        assert (func_view_bad(request).content ==
                b'<html><body>Dummy response.</body></html>')