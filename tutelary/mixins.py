import django.contrib.auth.mixins as base
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

from .models import check_perms
from .decorators import action_error_message


class PermissionRequiredMixin(base.PermissionRequiredMixin):
    """Permission checking mixin -- works just like the
    ``PermissionRequiredMixin`` in the default Django authentication
    system.

    """
    def has_permission(self):
        objs = [None]
        if hasattr(self, 'get_object'):
            try:
                # SingleObjectMixin with an existing object.
                objs = [self.get_object()]
            except:
                try:
                    # FormMixin for a new object.
                    objs = [self.get_form().save(commit=False)]
                except:
                    pass
        if objs == [None] and hasattr(self, 'get_queryset'):
            objs = self.get_queryset()
        return check_perms(self.request.user,
                           self.get_permission_required(),
                           objs, self.request.method)

    def get_permission_required(self):
        if self.permission_required is None:
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. Define '
                '{0}.permission_required, or override '
                '{0}.get_permission_required().'.format(
                    self.__class__.__name__)
            )

        if isinstance(self.permission_required, dict):
            perms = self.permission_required[self.request.method]
        else:
            perms = self.permission_required

        if callable(perms):
            perms = perms(self, self.request)

        if isinstance(perms, str):
            perms = (perms, )

        return perms

    def get_permission_denied_message(self):
        if self.permission_denied_message:
            return (self.permission_denied_message,)
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            return action_error_message(self.model.TutelaryMeta.actions,
                                        self.get_permission_required())

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(*self.get_permission_denied_message())
        super().handle_no_permission()
