import pytest
from tutelary.engine import Action
from tutelary.decorators import permissioned_model
from tutelary import mixins
from django.db import models
import django.views.generic as generic
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.core.exceptions import PermissionDenied
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
class CheckModel(models.Model):
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


class DummyRequest:
    def __init__(self, user, method='GET'):
        self.user = user
        self.method = method

    def get_full_path(self):
        return '/'

    def get_login_url(self):
        return '/account/login/'

    def get_redirect_field_name(self):
        return 'next'


def test_permission_required_single(datadir, setup):  # noqa
    class CheckViewBase(mixins.PermissionRequiredMixin, generic.DetailView):
        permission_required = 'check.detail'
        raise_exception = True

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

    user1, user2 = setup
    ok_obj = CheckModel(name='not-secret')
    secret_obj = CheckModel(name='secret')
    assert CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert CheckView1(ok_obj, user2).has_permission()
    assert CheckView1(secret_obj, user2).has_permission()


def test_permission_required_sequence(datadir, setup):  # noqa
    class CheckViewBase(mixins.PermissionRequiredMixin, generic.DetailView):
        permission_required = ('check.list', 'check.detail')
        raise_exception = True

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

    user1, user2 = setup
    ok_obj = CheckModel(name='not-secret')
    secret_obj = CheckModel(name='secret')
    assert CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert CheckView1(ok_obj, user2).has_permission()
    assert CheckView1(secret_obj, user2).has_permission()


def test_permission_required_callable(datadir, setup):  # noqa
    class CheckViewBase(mixins.PermissionRequiredMixin, generic.DetailView):
        def check_actions(self, view, request):
            if request.method == 'GET':
                return ('check.list', 'check.detail')
            elif request.method == 'POST':
                return 'check.create'
            else:
                return False

        permission_required = check_actions
        raise_exception = True

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

    user1, user2 = setup
    ok_obj = CheckModel(name='not-secret')
    secret_obj = CheckModel(name='secret')
    assert CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert CheckView1(ok_obj, user2).has_permission()
    assert CheckView1(secret_obj, user2).has_permission()


def test_permission_required_callable_false(datadir, setup):  # noqa
    class CheckViewBase(mixins.PermissionRequiredMixin, generic.DetailView):
        def check_actions(self, view, request):
            return False

        permission_required = check_actions
        raise_exception = True

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

    user1, user2 = setup
    ok_obj = CheckModel(name='not-secret')
    secret_obj = CheckModel(name='secret')
    assert not CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert not CheckView1(ok_obj, user2).has_permission()
    assert not CheckView1(secret_obj, user2).has_permission()


def test_permission_required_dict(datadir, setup):  # noqa
    class CheckViewBase(mixins.PermissionRequiredMixin, generic.DetailView):
        permission_required = {'GET': ('check.list', 'check.detail'),
                               'POST': 'check.create'}
        raise_exception = True

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

    user1, user2 = setup
    ok_obj = CheckModel(name='not-secret')
    secret_obj = CheckModel(name='secret')
    assert CheckView1(ok_obj, user1).has_permission()
    assert not CheckView1(secret_obj, user1).has_permission()
    assert CheckView1(ok_obj, user2).has_permission()
    assert CheckView1(secret_obj, user2).has_permission()


def patch_redirect_to_login(next, login_url, redirect_field_name):
    return HttpResponseRedirect('/login/')


def test_login_required(datadir, setup, monkeypatch):  # noqa
    request = DummyRequest(AnonymousUser())
    monkeypatch.setattr(mixins, 'redirect_to_login', patch_redirect_to_login)

    class CheckView(mixins.LoginPermissionRequiredMixin, generic.DetailView):
        permission_required = 'check.detail'

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = request

        def get_object(self):
            return self.obj

    ok_obj = CheckModel(name='not-secret')
    response = CheckView(ok_obj, AnonymousUser()).dispatch(request)
    assert response.status_code == 302


def test_login_required_raise_exception(datadir, setup):  # noqa
    request = DummyRequest(AnonymousUser())

    class CheckView(mixins.LoginPermissionRequiredMixin, generic.DetailView):
        permission_required = 'check.detail'
        raise_exception = True

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = request

        def get_object(self):
            return self.obj

    ok_obj = CheckModel(name='not-secret')
    with pytest.raises(PermissionDenied):
        CheckView(ok_obj, AnonymousUser()).dispatch(request)


def test_login_required_with_authenticated_user(datadir, setup):  # noqa
    user, user1 = setup
    request = DummyRequest(user)

    class CheckView(mixins.LoginPermissionRequiredMixin, generic.DetailView):
        permission_required = 'check.detail'
        raise_exception = True

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = request

        def get_object(self):
            return self.obj

    ok_obj = CheckModel(name='not-secret')
    response = CheckView(ok_obj, user).dispatch(request)
    assert response.status_code == 200


def test_missing_object(datadir, setup):  # noqa
    user, user1 = setup
    request = DummyRequest(user)

    class CheckView(mixins.LoginPermissionRequiredMixin, generic.DetailView):
        permission_required = 'check.detail'
        raise_exception = True

        def __init__(self, obj, user):
            self.model = obj
            self.obj = obj
            self.request = request

        def get_object(self):
            raise Http404()

    ok_obj = CheckModel(name='not-secret')
    with pytest.raises(Http404):
        CheckView(ok_obj, user).dispatch(request)
