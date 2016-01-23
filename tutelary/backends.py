from .base import Action, PermissionSet


class Backend:
    def has_perm(self, user, perm, obj=None, *args, **kwargs):
        # HANDLE ANONYMOUS USERS HERE.
        if not user.is_active:
            return False
        pset = PermissionSet(json=user.permissionset.first().data)
        return pset.allow(Action(perm), obj)
