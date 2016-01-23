import django.contrib.auth.mixins as base
from .base import Object


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    def has_permission(self):
        # ===> NEED TO DO SOMETHING ABOUT PERMISSIONS FOR ANONYMOUS
        #      USERS.  IT SHOULD BE POSSIBLE TO DO SOMETHING LIKE
        #      assign_user_policies(None, *policies) TO SET
        #      PERMISSIONS FOR UNAUTHENTICATED USERS.
        if not self.request.user.is_authenticated():
            return False
        obj = Object(self.model.TutelaryMeta.perm_type)
        try:
            if hasattr(self, 'get_object') and self.get_object() is not None:
                obj = self.get_object().get_permissions_object()
        except:
            pass
        perms = self.get_permission_required()
        allowed = self.model.TutelaryMeta.allowed_methods
        return all(self.request.user.has_perm(p, obj) for p in perms
                   if not (p in allowed and self.request.method in allowed[p]))
