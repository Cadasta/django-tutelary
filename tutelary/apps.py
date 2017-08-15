from django.apps import AppConfig
from django.apps import apps as django_apps
from django.conf import settings


class TutelaryConfig(AppConfig):
    name = 'tutelary'

    def ready(self):
        user_model = django_apps.get_model(settings.AUTH_USER_MODEL)
        if not hasattr(user_model, 'assign_policies'):
            from . import models
            user_model.assign_policies = models.assign_user_policies
            user_model.assigned_policies = models.user_assigned_policies
            user_model.permset_tree = models.permission_set_tree_property

        from django.contrib.auth.models import AnonymousUser
        AnonymousUser.permset_tree = models.permission_set_tree_property
