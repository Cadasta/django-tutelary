from django.core.exceptions import ImproperlyConfigured
from django.http.response import Http404
from rest_framework.exceptions import PermissionDenied
import rest_framework.generics as generic

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from tutelary.engine import Action
from tutelary.mixins import APIPermissionRequiredMixin

from .factories import UserFactory, PolicyFactory
from .datadir import datadir  # noqa
from .check_models import CheckModel1, CheckModel2, CheckModel4, CheckModel5


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


def api_get(url, user):
    req = APIRequestFactory().get(url)
    force_authenticate(req, user)
    return req


def api_post(url, user):
    req = APIRequestFactory().post(url)
    req.user = user
    req.successful_authenticator = True
    return req


class DummySerializer:
    data = 'dummy-data'

    def __init__(*args, **kwargs):
        pass

    def is_valid(self, *args, **kwargs):
        return True

    def save(self, *args, **kwargs):
        pass


class CheckViewBase(generic.RetrieveAPIView):
    object = None
    serializer_class = DummySerializer

    def __init__(self, *args, **kwargs):
        if 'object' in kwargs:
            self.model = kwargs['object']
            self.object = kwargs['object']


class CheckView1Base(APIPermissionRequiredMixin, CheckViewBase):
    permission_required = 'check.detail'
    raise_exception = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CheckView1(APIPermissionRequiredMixin, generic.RetrieveAPIView):
    object = None
    serializer_class = DummySerializer
    permission_required = 'check.detail'
    raise_exception = True

    def __init__(self, *args, **kwargs):
        if 'object' in kwargs:
            self.model = kwargs['object']
            self.object = kwargs['object']

    def get_perms_objects(self):
        return [self.object]

    def get_object(self):
        return self.object


class CheckView2(APIPermissionRequiredMixin, generic.ListAPIView):
    object = None
    serializer_class = DummySerializer
    permission_required = 'check.detail'
    raise_exception = True

    def __init__(self, *args, **kwargs):
        if 'object' in kwargs:
            self.model = kwargs['object']
            self.object = kwargs['object']

    def get_queryset(self):
        return [self.object]


def test_mixin_basic_obj_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok = CheckModel1(name='not-secret')
    secret = CheckModel1(name='secret')

    req1 = api_get('/check', user1)
    rsp1 = CheckView1().as_view(object=ok)(req1).render()
    assert rsp1.status_code == 200
    rsp2 = CheckView1().as_view(object=secret)(req1).render()
    assert rsp2.status_code == 403

    req2 = api_get('/check', user2)
    rsp3 = CheckView1().as_view(object=ok)(req2).render()
    assert rsp3.status_code == 200
    rsp4 = CheckView1().as_view(object=secret)(req2).render()
    assert rsp4.status_code == 200


def test_mixin_basic_queryset_path(datadir, setup):  # noqa
    user1, user2 = setup
    ok = CheckModel1(name='not-secret')
    secret = CheckModel1(name='secret')

    req1 = api_get('/check', user1)
    rsp1 = CheckView2().as_view(object=ok)(req1).render()
    assert rsp1.status_code == 200
    rsp2 = CheckView2().as_view(object=secret)(req1).render()
    assert rsp2.status_code == 403

    req2 = api_get('/check', user2)
    rsp3 = CheckView2().as_view(object=ok)(req2).render()
    assert rsp3.status_code == 200
    rsp4 = CheckView2().as_view(object=secret)(req2).render()
    assert rsp4.status_code == 200


def test_view_exceptions_no_policies(datadir, setup):  # noqa
    other_user = UserFactory.create(username='other')
    ok = CheckModel1(name='not-secret')
    req = api_get('/check', other_user)
    rsp = CheckView1().as_view(object=ok)(req).render()
    assert rsp.status_code == 403


def test_view_exceptions_no_permission_required(datadir, setup):  # noqa
    class CheckViewBad(APIPermissionRequiredMixin, generic.RetrieveAPIView):
        object = None
        serializer_class = DummySerializer
        raise_exception = True

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']

        def get_object(self):
            return self.object

    user1, user2 = setup
    ok = CheckModel1(name='not-secret')
    req = api_get('/check', user1)
    with pytest.raises(ImproperlyConfigured):
        rsp = CheckViewBad().as_view(object=ok)(req).render()  # noqa


def test_error_messages(datadir, setup):  # noqa
    class CheckCreateView(APIPermissionRequiredMixin, generic.CreateAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check.create'
        raise_exception = True

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']

        def get_object(self):
            return self.object

    class CheckCreateView2(APIPermissionRequiredMixin, generic.CreateAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check.create'
        permission_denied_message = 'special message'
        raise_exception = False

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']

        def get_object(self):
            return self.object

    class CheckCreateView3(APIPermissionRequiredMixin, generic.CreateAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check.create'
        raise_exception = False

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']

        def get_object(self):
            return self.object

    # We use this to temporarily monkeypatch the handle_no_permission
    # method in the APIPermissionRequiredMixin class to check that we
    # get routed there correctly if raise_exception isn't set.
    def tmp(mixin, request, message):
        raise PermissionDenied('test fixup message')

    user1, user2 = setup
    other_user = UserFactory.create(username='other')
    obj = CheckModel1(name='secret')

    req1 = api_get('/check', other_user)
    rsp1 = CheckView1().as_view(object=obj)(req1).render()
    assert rsp1.status_code == 403
    assert rsp1.data['detail'] == 'detail view not allowed'

    req2 = api_post('/check', user1)
    rsp2 = CheckCreateView().as_view(object=obj)(req2).render()
    assert rsp2.status_code == 403
    assert rsp2.data['detail'] == 'Permission denied.'

    rsp2a = CheckCreateView2().as_view(object=obj)(req2).render()
    assert rsp2a.status_code == 403
    assert rsp2a.data['detail'] == 'special message'

    safe = generic.CreateAPIView.permission_denied
    try:
        generic.CreateAPIView.permission_denied = tmp
        rsp3 = CheckCreateView3().as_view(object=obj)(req2).render()
    finally:
        generic.CreateAPIView.permission_denied = safe
    assert rsp3.status_code == 403
    assert rsp3.data['detail'] == 'test fixup message'


def test_mixin_fk_obj_path(datadir, setup):  # noqa
    class Check2View1(APIPermissionRequiredMixin, generic.CreateAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check2.create'
        raise_exception = True

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']

        def get_object(self):
            return self.object

    user1, user2 = setup
    ok_container = CheckModel1(name='not-secret')
    secret_container = CheckModel1(name='secret')
    ok = CheckModel2(name='visible', container=ok_container)
    secret = CheckModel2(name='not-visible', container=secret_container)

    req1 = api_post('/check', user1)
    rsp1 = Check2View1().as_view(object=ok)(req1).render()
    assert rsp1.status_code == 403
    rsp2 = Check2View1().as_view(object=secret)(req1).render()
    assert rsp2.status_code == 403
    req2 = api_post('/check', user2)
    rsp3 = Check2View1().as_view(object=ok)(req2).render()
    assert rsp3.status_code == 201
    rsp4 = Check2View1().as_view(object=secret)(req2).render()
    assert rsp4.status_code == 201


def test_mixin_fk_queryset_path(datadir, setup):  # noqa
    class Check2View2(APIPermissionRequiredMixin, generic.ListAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check2.list'
        raise_exception = True

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']

        def get_queryset(self):
            return [self.object]

    user1, user2 = setup
    ok_container = CheckModel1(name='not-secret')
    secret_container = CheckModel1(name='secret')
    ok = CheckModel2(name='visible', container=ok_container)
    secret = CheckModel2(name='not-visible', container=secret_container)

    req1 = api_get('/check', user1)
    rsp1 = Check2View2().as_view(object=ok)(req1).render()
    assert rsp1.status_code == 200
    rsp2 = Check2View2().as_view(object=secret)(req1).render()
    assert rsp2.status_code == 403
    req2 = api_get('/check', user2)
    rsp3 = Check2View2().as_view(object=ok)(req2).render()
    assert rsp3.status_code == 200
    rsp4 = Check2View2().as_view(object=secret)(req2).render()
    assert rsp4.status_code == 200


def test_mixin_null_perms_obj(datadir, setup):  # noqa
    class Check4ListView(APIPermissionRequiredMixin, generic.ListAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check4.list'

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']
            else:
                self.object = None

        def get_queryset(self):
            if self.object is not None:
                return [self.object]
            else:
                return []

    class Check4CreateView(APIPermissionRequiredMixin, generic.CreateAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check4.create'

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']
            else:
                self.object = None

        def get_object(self):
            if self.object is not None:
                return self.object
            else:
                raise Http404('No object')

    user1, user2 = setup
    obj = CheckModel4(name='visible')
    new_obj = CheckModel4(name='new-one')

    req1 = api_get('/check', user1)
    rsp1 = Check4ListView().as_view(object=obj)(req1).render()
    assert rsp1.status_code == 200
    req2 = api_post('/check', user1)
    rsp2 = Check4CreateView().as_view(object=new_obj)(req2).render()
    assert rsp2.status_code == 403

    req3 = api_get('/check', user2)
    rsp3 = Check4ListView().as_view(object=obj)(req3).render()
    assert rsp3.status_code == 200
    req4 = api_post('/check', user2)
    rsp4 = Check4CreateView().as_view(object=new_obj)(req4).render()
    assert rsp4.status_code == 201

    req5 = api_get('/check', user2)
    rsp5 = Check4ListView().as_view(object=None)(req5).render()
    assert rsp5.status_code == 200


def test_mixin_no_permissions_object(datadir, setup):  # noqa
    class Check5DetailView(APIPermissionRequiredMixin,
                           generic.RetrieveAPIView):
        object = None
        serializer_class = DummySerializer
        permission_required = 'check5.detail'

        def __init__(self, *args, **kwargs):
            if 'object' in kwargs:
                self.model = kwargs['object']
                self.object = kwargs['object']
            else:
                self.object = None

        def get_object(self):
            if self.object is not None:
                return self.object
            else:
                raise Http404('No object')

    user1, user2 = setup
    obj = CheckModel5(name='check')

    req1 = api_get('/check', user1)
    rsp1 = Check5DetailView().as_view(object=obj)(req1).render()
    assert rsp1.status_code == 403
    req2 = api_get('/check', user2)
    rsp2 = Check5DetailView().as_view(object=obj)(req2).render()
    assert rsp2.status_code == 200
    req3 = api_get('/check', user1)
    rsp3 = Check5DetailView().as_view(object=None)(req3).render()
    assert rsp3.status_code == 404
