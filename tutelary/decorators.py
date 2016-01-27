from functools import reduce
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.db import models

from .base import Object, Action
from .exceptions import DecoratorException


def permission_required(*actions, raise_exception=False):
    def check_perms(user):
        if user.is_authenticated() and all(user.has_perms(a) for a in actions):
            return True
        if raise_exception:
            raise PermissionDenied
        else:
            return False
    return user_passes_test(check_perms)


def get_path_fields(cls, base=[]):
    pfs = []
    for pf in cls.TutelaryMeta.path_fields:
        if pf == 'pk':
            pfs.append(base + ['pk'])
        else:
            f = cls._meta.get_field(pf)
            if isinstance(f, models.ForeignKey):
                pfs += get_path_fields(f.target_field.model, base=base + [pf])
            else:
                pfs.append(base + [f.name])
    return pfs


def get_permissions_object(obj):
    def get_one(pf):
        if isinstance(pf, str):
            return pf
        else:
            return str(reduce(lambda o, f: getattr(o, f), pf, obj))
    return Object([get_one(pf) for pf in obj.__class__.TutelaryMeta.pfs])


def permissioned_model(cls, perm_type=None, path_fields=None, actions=None):
    """Function to set up a model for permissioning.  Can either be called
    directly, passing a class and suitable values for ``perm_type``,
    ``path_fields`` and ``actions``, or can be used as a class
    decorator, taking values for ``perm_type``, ``path_fields`` and
    ``actions`` from the ``TutelaryMeta`` subclass of the decorated
    class.

    """
    if not (hasattr(cls, 'TutelaryMeta') or
            perm_type is None or path_fields is None or actions is None):
        cls.TutelaryMeta = type('TutelaryMeta', (object,),
                                dict(perm_type=perm_type,
                                     path_fields=path_fields,
                                     actions=actions))
    if hasattr(cls, 'TutelaryMeta'):
        cls.TutelaryMeta.pfs = ([cls.TutelaryMeta.perm_type] +
                                get_path_fields(cls))
        cls.TutelaryMeta.allowed_methods = {}
        cls.get_permissions_object = get_permissions_object
        for a in cls.TutelaryMeta.actions:
            Action.register(a[0])
            if len(a) > 2:
                cls.TutelaryMeta.allowed_methods[a[0]] = a[2]
    else:
        raise DecoratorException('permissioned_model',
                                 "missing TutelaryMeta member in '" +
                                 cls.__name__ + "'")
    return cls
