import django.contrib.auth.mixins as base
from .engine import Object


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    """Permission checking mixin -- works just like the
    ``PermissionRequiredMixin`` in the default Django authentication
    system.

    """
    def has_permission(self):
        obj = None
        get_allowed = {}
        perms_obj = {}
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            obj = Object(self.model.TutelaryMeta.perm_type)
            get_allowed = self.model.TutelaryMeta.get_allowed
            perms_obj = self.model.TutelaryMeta.perms_obj
        try:
            if hasattr(self, 'get_object') and self.get_object() is not None:
                obj = self.get_object().get_permissions_object()
        except:
            pass
        for p in self.get_permission_required():
            test_obj = obj
            if p in perms_obj:
                po = perms_obj[p]
                if obj is None and po is not None:
                    return False
                if po is None:
                    test_obj = None
                else:
                    test_obj = getattr(obj, po)
            if not self.request.user.has_perm(p, test_obj):
                if not (p in get_allowed and self.request.method == 'GET'):
                    return False
        return True
