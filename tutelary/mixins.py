import django.contrib.auth.mixins as base


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
        elif hasattr(self, 'get_queryset'):
            objs = self.get_queryset()
        for p in self.get_permission_required():
            for o in objs:
                test_obj = None
                if o is not None:
                    test_obj = o.get_permissions_object(p)
                if not self.request.user.has_perm(p, test_obj):
                    if not (p in get_allowed and self.request.method == 'GET'):
                        return False
        return True
