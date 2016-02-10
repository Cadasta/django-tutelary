from functools import reduce
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.db import models

from .engine import Object, Action
from .exceptions import DecoratorException, PermissionObjectException


def permission_required(*actions, obj=None, raise_exception=False):
    """Permission checking decorator -- works like the
    ``permission_required`` decorator in the default Django
    authentication system, except that it takes a sequence of actions
    to check, an object must be supplied, and the user must have
    permission to perform all of the actions on the given object for
    the permissions test to pass.  *Not actually sure how useful this
    is going to be: in any case where obj is not None, it's going to
    be tricky to get the object into the decoratory.  Class-based
    views are definitely best here...*

    """
    def check_perms(user):
        if user.is_authenticated() and all(user.has_perms(a, obj)
                                           for a in actions):
            return True
        if raise_exception:
            raise PermissionDenied
        else:
            return False
    return user_passes_test(check_perms)


def get_path_fields(cls, base=[]):
    """Get object fields used for calculation of django-tutelary object
    paths.

    """
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


def get_perms_object(obj, action):
    """Get the django-tutelary path for an object, based on the fields
    listed in ``TutelaryMeta.pfs``.

    """
    def get_one(pf):
        if isinstance(pf, str):
            return pf
        else:
            return str(reduce(lambda o, f: getattr(o, f), pf, obj))
    return Object([get_one(pf) for pf in obj.__class__.TutelaryMeta.pfs])


def make_get_perms_object(perms_objs):
    """Make a function to delegate permission object rendering to some
    other (foreign key) field of an object.

    """
    def retfn(obj, action):
        if action in perms_objs:
            if perms_objs[action] is None:
                return None
            else:
                return get_perms_object(getattr(obj, perms_objs[action]),
                                        action)
        else:
            return get_perms_object(obj, action)
    return retfn


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
        cls.TutelaryMeta.get_allowed = {}
        perms_objs = {}
        for a in cls.TutelaryMeta.actions:
            an = a
            ap = {}
            if isinstance(a, tuple):
                an = a[0]
                ap = a[1]
            Action.register(an)
            if 'get_allowed' in ap:
                cls.TutelaryMeta.get_allowed[an] = ap['get_allowed']
            if 'permissions_object' in ap:
                po = ap['permissions_object']
                if po is not None:
                    tst_class = getattr(cls, po).field.__class__
                    if (not hasattr(cls, po) or
                        (tst_class not in
                         [models.ForeignKey, models.OneToOneField])):
                        raise PermissionObjectException(po)
                perms_objs[an] = po
        if len(perms_objs) == 0:
            cls.get_permissions_object = get_perms_object
        else:
            cls.get_permissions_object = make_get_perms_object(perms_objs)
    else:
        raise DecoratorException('permissioned_model',
                                 "missing TutelaryMeta member in '" +
                                 cls.__name__ + "'")
    return cls
