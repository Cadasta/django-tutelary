from django.core.exceptions import ObjectDoesNotExist
from .models import PermissionSet as PermissionSetModel
from .base import Action, PermissionSet


class Backend:
    def get_pset(self, user):
        if user.is_authenticated():
            return PermissionSet(json=user.permissionset.first().data)
        else:
            apset = PermissionSetModel.objects.get(anonymous_user=True)
            return PermissionSet(json=apset.data)

    def has_perm(self, user, perm, obj=None, *args, **kwargs):
        try:
            return self.get_pset(user).allow(Action(perm), obj)
        except ObjectDoesNotExist:
            return False

    def permitted_actions(self, user, obj=None):
        try:
            return self.get_pset(user).permitted_actions(obj)
        except ObjectDoesNotExist:
            return []
