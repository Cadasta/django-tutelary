from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test


def permission_required(*actions, raise_exception=False):
    def check_perms(user):
        if all(user.has_perms(a) for a in actions):
            return True
        if raise_exception:
            raise PermissionDenied
        else:
            return False
    return user_passes_test(check_perms)
