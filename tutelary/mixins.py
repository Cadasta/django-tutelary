import django.contrib.auth.mixins as base


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    def has_permission(self):
        # ===> NEED TO DO SOMETHING ABOUT PERMISSIONS FOR ANONYMOUS
        #      USERS.  IT SHOULD BE POSSIBLE TO DO SOMETHING LIKE
        #      assign_user_policies(None, *policies) TO SET
        #      PERMISSIONS FOR UNAUTHENTICATED USERS.
        if not self.request.user.is_authenticated():
            return False
        return all(p == 'user.list' or self.request.user.has_perm(p)
                   for p in self.get_permission_required())
