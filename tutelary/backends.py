from django.contrib.auth.backends import ModelBackend


class BackendMixin:
    def get_user_permissions(self, user, obj=None):
        print('get_user_permissions: ', user, obj)
        return set()

    def get_group_permissions(self, user, obj=None):
        print('get_group_permissions: ', user, obj)
        return set()

    def get_all_permissions(self, user, obj=None):
        print('get_all_permissions: ', user, obj)
        if not user.is_active or user.is_anonymous() or obj is not None:
            return set()
        if not hasattr(user, '_perm_cache'):
            user._perm_cache = self.get_user_permissions(user)
            user._perm_cache.update(self.get_group_permissions(user))
        return user._perm_cache

    def has_perm(self, user, perm, obj=None):
        print('has_perm: ', user, perm, obj)
        if not user.is_active:
            return False
        return perm in self.get_all_permissions(user, obj)

    def has_module_perms(self, user, app_label):
        print('has_module_perm: ', user, app_label)
        if not user.is_active:
            return False
        for perm in self.get_all_permissions(user):
            if perm[:perm.index('.')] == app_label:
                return True
        return False


class Backend(BackendMixin, ModelBackend):
    pass
