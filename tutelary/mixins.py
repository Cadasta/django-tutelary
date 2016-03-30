from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from collections.abc import Sequence

from .models import check_perms
from .decorators import action_error_message


class BasePermissionRequiredMixin:
    def get_permission_required(self):
        if (not hasattr(self, 'permission_required') or
           self.permission_required is None):
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. Define '
                '{0}.permission_required, or override '
                '{0}.get_permission_required().'.format(
                    self.__class__.__name__)
            )

        perms = self.permission_required
        if isinstance(self.permission_required, dict):
            if self.request.method in self.permission_required:
                perms = self.permission_required[self.request.method]

        if callable(perms):
            perms = perms(self, self.request)

        if isinstance(perms, str):
            perms = (perms, )

        return perms

    def get_permission_denied_message(self, default=None):
        if hasattr(self, 'permission_denied_message'):
            return (self.permission_denied_message,)
        if hasattr(self, 'model') and hasattr(self.model, 'TutelaryMeta'):
            return action_error_message(self.model.TutelaryMeta.actions,
                                        self.get_permission_required(),
                                        default)

    def get_queryset(self):
        if hasattr(self, 'filtered_queryset'):
            return self.filtered_queryset
        elif hasattr(super(), 'get_queryset'):
            return super().get_queryset()
        else:
            return [None]

    def perms_filter_queryset(self, objs):
        actions = self.get_permission_required()
        if isinstance(self.permission_filter_queryset, Sequence):
            actions += tuple(self.permission_filter_queryset)

        def check_one(obj):
            return check_perms(self.request.user, actions,
                               [obj], self.request.method)

        filtered_pks = [o.pk for o in filter(check_one, objs)]
        self.filtered_queryset = self.get_queryset().filter(
            pk__in=filtered_pks
        )


class PermissionRequiredMixin(BasePermissionRequiredMixin):
    """Permission checking mixin -- works just like the
    ``PermissionRequiredMixin`` in the default Django authentication
    system.

    """
    def has_permission(self):
        """Permission checking for "normal" Django."""
        objs = [None]
        if hasattr(self, 'get_perms_objects'):
            objs = self.get_perms_objects()
        else:
            if hasattr(self, 'get_object'):
                try:
                    objs = [self.get_object()]
                except:
                    try:
                        objs = [self.get_form().save(commit=False)]
                    except:
                        pass
            if objs == [None]:
                objs = self.get_queryset()

        if (hasattr(self, 'permission_filter_queryset') and
           self.permission_filter_queryset is not False and
           self.request.method == 'GET'):
            if objs != [None]:
                self.perms_filter_queryset(objs)
            return True
        else:
            return check_perms(self.request.user,
                               self.get_permission_required(),
                               objs, self.request.method)

    def handle_no_permission(self):
        msg = self.get_permission_denied_message()
        if hasattr(self, 'raise_exception') and self.raise_exception:
            raise PermissionDenied(*msg)
        return msg

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class APIPermissionRequiredMixin(BasePermissionRequiredMixin):
    """Permission checking mixin for Django Rest Framework -- works just
    like the ``PermissionRequiredMixin`` in the default Django
    authentication system.

    """
    def check_permissions(self, request):
        """Permission checking for DRF."""
        objs = [None]
        if hasattr(self, 'get_perms_objects'):
            objs = self.get_perms_objects()
        else:
            if hasattr(self, 'get_object'):
                try:
                    objs = [self.get_object()]
                except:
                    pass
                if objs == [None]:
                    objs = self.get_queryset()
                if len(objs) == 0:
                    objs = [None]

        if (hasattr(self, 'permission_filter_queryset') and
           self.permission_filter_queryset is not False and
           self.request.method == 'GET'):
            if objs != [None]:
                self.perms_filter_queryset(objs)
        else:
            has_perm = check_perms(self.request.user,
                                   self.get_permission_required(),
                                   objs, self.request.method)

            if not has_perm:
                msg = self.get_permission_denied_message(
                    default="Permission denied."
                )
                if isinstance(msg, Sequence):
                    msg = msg[0]
                self.permission_denied(request, message=msg)

    def initial(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().initial(request, *args, **kwargs)
