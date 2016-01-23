from django.core.exceptions import ObjectDoesNotExist
from .models import PermissionSet as PermissionSetModel
from .base import Action, PermissionSet


class Backend:
    def has_perm(self, user, perm, obj=None, *args, **kwargs):
        if user.is_authenticated():
            pset = PermissionSet(json=user.permissionset.first().data)
        else:
            try:
                apset = PermissionSetModel.objects.get(anonymous_user=True)
            except ObjectDoesNotExist:
                return False
            pset = PermissionSet(json=apset.data)
        return pset.allow(Action(perm), obj)
