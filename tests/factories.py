import os.path
import factory

from tutelary.models import Policy, Role
from django.contrib.auth.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User


class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    @classmethod
    def set_directory(cls, dir):
        cls.directory = dir

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        body_file = os.path.join(cls.directory, kwargs.pop('file', None))
        kwargs['body'] = open(body_file).read()
        return kwargs


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role
