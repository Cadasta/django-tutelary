import django.contrib.auth.mixins as base
from .engine import Object


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    """Permission checking mixin -- works just like the
    ``PermissionRequiredMixin`` in the default Django authentication
    system.

    """
    def has_permission(self):
        obj = None
        perms_obj = None
        get_allowed = {}
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            perms_obj = Object(self.model.TutelaryMeta.perm_type)
            get_allowed = self.model.TutelaryMeta.get_allowed
        try:
            if hasattr(self, 'get_object') and self.get_object() is not None:
                obj = self.get_object()
                perms_obj = obj.get_permissions_object()
        except:
            pass
        for p in self.get_permission_required():
            if callable(perms_obj):
                test_obj = perms_obj(p, obj)
            else:
                test_obj = perms_obj
            if not self.request.user.has_perm(p, test_obj):
                if not (p in get_allowed and self.request.method == 'GET'):
                    return False
        return True
