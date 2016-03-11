from functools import reduce, wraps
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.decorators import available_attrs

from .engine import Object, Action
from .models import check_perms
from .exceptions import DecoratorException, PermissionObjectException


def permission_required(*actions, obj=None, raise_exception=False):
    """Permission checking decorator -- works like the
    ``permission_required`` decorator in the default Django
    authentication system, except that it takes a sequence of actions
    to check, an object must be supplied, and the user must have
    permission to perform all of the actions on the given object for
    the permissions test to pass.  *Not actually sure how useful this
    is going to be: in any case where obj is not None, it's going to
    be tricky to get the object into the decorator.  Class-based views
    are definitely best here...*

    """
    def checker(user):
        ok = False
        if user.is_authenticated() and check_perms(user, actions, [obj]):
            ok = True
        if raise_exception and not ok:
            raise PermissionDenied
        else:
            return ok

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if checker(request.user):
                return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


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
    if not issubclass(cls, models.Model):
        raise DecoratorException(
            'permissioned_model',
            "class '" + cls.__name__ + "' is not a Django model"
        )
    added = False
    try:
        if not hasattr(cls, 'TutelaryMeta'):
            if perm_type is None or path_fields is None or actions is None:
                raise DecoratorException(
                    'permissioned_model',
                    ("missing argument: all of perm_type, path_fields and " +
                     "actions must be supplied")
                )
            added = True
            cls.TutelaryMeta = type('TutelaryMeta', (object,),
                                    dict(perm_type=perm_type,
                                         path_fields=path_fields,
                                         actions=actions))
        cls.TutelaryMeta.pfs = ([cls.TutelaryMeta.perm_type] +
                                get_path_fields(cls))
        perms_objs = {}
        for a in cls.TutelaryMeta.actions:
            an = a
            ap = {}
            if isinstance(a, tuple):
                an = a[0]
                ap = a[1]
            Action.register(an)
            if isinstance(ap, dict) and 'permissions_object' in ap:
                po = ap['permissions_object']
                if po is not None:
                    try:
                        t = cls._meta.get_field(po).__class__
                        if t not in [models.ForeignKey,
                                     models.OneToOneField]:
                            raise PermissionObjectException(po)
                    except:
                        raise PermissionObjectException(po)
                perms_objs[an] = po
        if len(perms_objs) == 0:
            cls.get_permissions_object = get_perms_object
        else:
            cls.get_permissions_object = make_get_perms_object(perms_objs)
        return cls
    except:
        if added:
            del cls.TutelaryMeta
        raise


def action_error_message(actions, req_actions, default=None):
    for req in req_actions:
        for a in actions:
            if isinstance(a, tuple) and a[0] == req:
                if 'error_message' in a[1]:
                    return (a[1]['error_message'],)
    if default is not None:
        return (default,)
    else:
        return ()
