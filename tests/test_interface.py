from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.contrib.auth import get_backends
from django.db import models
from django.http import HttpResponse
import django.views.generic as generic
import django.views.generic.edit as edit

import pytest
from django.test import RequestFactory

from tutelary.engine import Action
from tutelary.decorators import permissioned_model, permission_required
from tutelary.mixins import PermissionRequiredMixin
from tutelary.exceptions import (
    PermissionObjectException, DecoratorException,
    InvalidPermissionObjectException
)

from .factories import UserFactory, PolicyFactory
from .datadir import datadir  # noqa
from .check_models import (
    CheckModel1, CheckModel2, CheckModel3, CheckModel4, CheckModel5,
    CheckModel1Broken
)


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


class CheckViewBase:
    def __init__(self, obj, user):
        self.model = obj
        self.obj = obj
        self.request = RequestFactory().get('/check')
        self.request.user = user


class CheckView1Base(PermissionRequiredMixin, CheckViewBase,
                     generic.DetailView):
    permission_required = 'check.detail'
    raise_exception = True


class CheckView1(CheckView1Base):
    def get_perms_objects(self):
        return [self.obj]

    def get_object(self):
        return self.obj


class CheckView2(CheckView1Base):
    def get_queryset(self):
        if self.obj is not None:
            return [self.obj]
        else:
            return []


def test_mixin_basic_obj_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok_obj = CheckModel1(name='not-secret')
    secret_obj = CheckModel1(name='secret')

    assert CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert CheckView1(ok_obj, user2).has_permission()
    assert CheckView1(secret_obj, user2).has_permission()
    view1 = CheckView1(ok_obj, user1)
    view1.dispatch(view1.request)


def test_mixin_basic_queryset_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok_obj = CheckModel1(name='not-secret')
    secret_obj = CheckModel1(name='secret')

    assert CheckView2(ok_obj, user1).has_permission()
    assert not CheckView2(secret_obj, user1).has_permission()
    assert CheckView2(ok_obj, user2).has_permission()
    assert CheckView2(secret_obj, user2).has_permission()
    assert CheckView2(None, user2).has_permission()


def test_view_exceptions_no_policies(datadir, setup):  # noqa
    other_user = UserFactory.create(username='other')
    ok_obj = CheckModel1(name='not-secret')
    assert not CheckView1(ok_obj, other_user).has_permission()


def test_view_exceptions_no_permission_required(datadir, setup):  # noqa
    class CheckViewBad(PermissionRequiredMixin, CheckViewBase,
                       generic.DetailView):
        raise_exception = True

        def get_object(self):
            return self.obj

    user1, user2 = setup
    ok_obj = CheckModel1(name='not-secret')
    with pytest.raises(ImproperlyConfigured):
        CheckViewBad(ok_obj, user1).has_permission()


def test_error_messages(datadir, setup):  # noqa
    class CheckCreateView(PermissionRequiredMixin, CheckViewBase,
                          edit.CreateView):
        permission_required = 'check.create'
        raise_exception = True

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = RequestFactory().post('/check')
            self.request.user = user

        def get_object(self):
            return self.obj

    class CheckCreateView2(PermissionRequiredMixin, edit.CreateView):
        permission_required = 'check.create'
        permission_denied_message = 'special message'
        raise_exception = True

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = RequestFactory().post('/check')
            self.request.user = user

        def get_object(self):
            return self.obj

    class CheckCreateView3(PermissionRequiredMixin, edit.CreateView):
        raise_exception = False
        permission_required = 'check.create'

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = RequestFactory().post('/check')
            self.request.user = user

        def get_object(self):
            return self.obj

        def handle_no_permission(self):
            raise PermissionDenied('test fixup message')

    user1, user2 = setup
    other_user = UserFactory.create(username='other')
    obj = CheckModel1(name='secret')
    view1 = CheckView1(obj, other_user)
    with pytest.raises(PermissionDenied) as exc_info1:
        view1.dispatch(view1.request)
    assert exc_info1.value.args == ('detail view not allowed',)
    view2 = CheckCreateView(obj, user1)
    with pytest.raises(PermissionDenied) as exc_info2:
        view2.dispatch(view2.request)
    assert exc_info2.value.args == ()
    view3 = CheckCreateView2(obj, user1)
    with pytest.raises(PermissionDenied) as exc_info3:
        view3.dispatch(view3.request)
    assert exc_info3.value.args == ('special message',)
    view4 = CheckCreateView3(obj, user1)
    with pytest.raises(PermissionDenied) as exc_info4:
        view4.dispatch(view4.request)
    assert exc_info4.value.args == ('test fixup message',)


class Check2ViewBase(PermissionRequiredMixin, CheckViewBase, generic.ListView):
    permission_required = 'check2.list'


def test_mixin_fk_obj_path(datadir, setup):  # noqa
    class Check2View1(Check2ViewBase):
        def get_object(self):
            return self.obj

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
    class Check2View2(Check2ViewBase):
        def get_queryset(self):
            return [self.obj]

    user1, user2 = setup
    ok_container = CheckModel1(name='not-secret')
    secret_container = CheckModel1(name='secret')
    ok_obj = CheckModel2(name='visible', container=ok_container)
    secret_obj = CheckModel2(name='not-visible', container=secret_container)

    assert Check2View2(ok_obj, user1).has_permission()
    assert not Check2View2(secret_obj, user1).has_permission()
    assert Check2View2(ok_obj, user2).has_permission()
    assert Check2View2(secret_obj, user2).has_permission()


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


def test_mixin_null_perms_obj(datadir, setup):  # noqa
    class Check4ListView(PermissionRequiredMixin, CheckViewBase,
                         generic.ListView):
        permission_required = 'check4.list'

        def get_object(self):
            return self.obj

    class Check4CreateView(PermissionRequiredMixin, edit.CreateView):
        permission_required = 'check4.create'

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = RequestFactory().post('/check')
            self.request.user = user

        def get_object(self):
            return self.obj

    user1, user2 = setup
    obj = CheckModel4(name='visible')
    new_obj = CheckModel4(name='new-one')

    assert Check4ListView(obj, user1).has_permission()
    assert not Check4CreateView(new_obj, user1).has_permission()
    assert Check4ListView(obj, user2).has_permission()
    assert Check4CreateView(new_obj, user2).has_permission()


def test_mixin_no_permissions_object(datadir, setup):  # noqa
    class Check5DetailView(PermissionRequiredMixin, CheckViewBase,
                           generic.DetailView):
        permission_required = 'check5.detail'

        def get_object(self):
            return self.obj

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


def test_backend_exceptions(datadir, setup):  # noqa
    user1, user2 = setup
    ok_obj = CheckModel1(name='secret')
    broken_obj = CheckModel1Broken(name='broken')

    assert not user1.has_perm('check.detail', ok_obj)
    assert user2.has_perm('check.detail', ok_obj)
    with pytest.raises(InvalidPermissionObjectException):
        assert not user1.has_perm('check.detail', broken_obj)
    with pytest.raises(InvalidPermissionObjectException):
        assert user2.has_perm('check.detail', broken_obj)

    with pytest.raises(InvalidPermissionObjectException):
        assert get_backends()[0].permitted_actions(user1, ok_obj) != []
