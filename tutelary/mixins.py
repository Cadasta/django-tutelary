import django.contrib.auth.mixins as base
from .base import Object


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    def has_permission(self):
        obj = None
        allowed = {}
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            obj = Object(self.model.TutelaryMeta.perm_type)
            allowed = self.model.TutelaryMeta.allowed_methods
        try:
            if hasattr(self, 'get_object') and self.get_object() is not None:
                obj = self.get_object().get_permissions_object()
        except:
            pass
        perms = self.get_permission_required()
        return all(self.request.user.has_perm(p, obj) for p in perms
                   if not (p in allowed and self.request.method in allowed[p]))
