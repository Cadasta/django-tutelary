from django.core.exceptions import ObjectDoesNotExist
from .models import PermissionSet as PermissionSetModel
from .engine import Action, PermissionSet


class Backend:
    """Custom authentication backend: dispatches ``has_perm`` queries to
    the user's permission set.

    """
    def _get_pset(self, user):
        if user.is_authenticated():
            return PermissionSet(json=user.permissionset.first().data)
        else:
            apset = PermissionSetModel.objects.get(anonymous_user=True)
            return PermissionSet(json=apset.data)

    def has_perm(self, user, perm, obj=None, *args, **kwargs):
        """Test user permissions for a single action and object.

        :param user: The user to test.
        :type user: ``User``
        :param perm: The action to test.
        :type perm: ``str``
        :param obj: The object path to test.
        :type obj: ``tutelary.engine.Object``
        :returns: ``bool`` -- is the action permitted?
        """
        try:
            return self._get_pset(user).allow(Action(perm), obj)
        except ObjectDoesNotExist:
            return False

    def permitted_actions(self, user, obj=None):
        """Determine list of permitted actions for an object or object
        pattern.

        :param user: The user to test.
        :type user: ``User``
        :param obj: The object path to test.
        :type obj: ``tutelary.engine.Object``
        :returns: ``list(tutelary.engine.Action)`` -- permitted actions.

        """
        try:
            return self._get_pset(user).permitted_actions(obj)
        except ObjectDoesNotExist:
            return []
