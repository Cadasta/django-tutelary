import django.contrib.auth.mixins as base


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    def has_permission(self):
        return all(self.request.user.has_perms(p)
                   for p in self.get_permission_required())
