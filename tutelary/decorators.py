from functools import reduce
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.db import models


def permission_required(*actions, raise_exception=False):
    def check_perms(user):
        if all(user.has_perms(a) for a in actions):
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


def get_permissions_path(obj):
    def get_one(pf):
        if isinstance(pf, str):
            return pf
        else:
            return str(reduce(lambda o, f: getattr(o, f), pf, obj))
    return '/'.join(map(get_one, obj.__class__.TutelaryMeta.pfs))


def permissioned_model(cls):
    if hasattr(cls, 'TutelaryMeta'):
        cls.TutelaryMeta.pfs = [cls.TutelaryMeta.type] + get_path_fields(cls)
        cls.get_permissions_path = get_permissions_path
    return cls
