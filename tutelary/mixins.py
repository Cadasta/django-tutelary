import django.contrib.auth.mixins as base

from .models import check_perms


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    """Permission checking mixin -- works just like the
    ``PermissionRequiredMixin`` in the default Django authentication
    system.

    """
    def has_permission(self):
        objs = [None]
        get_allowed = {}
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            get_allowed = self.model.TutelaryMeta.get_allowed
        if hasattr(self, 'get_object'):
            try:
                objs = [self.get_object()]
            except:
                pass
        if objs == [None] and hasattr(self, 'get_queryset'):
            objs = self.get_queryset()
        return check_perms(self.request.user,
                           self.get_permission_required(),
                           objs, get_allowed, self.request.method)
