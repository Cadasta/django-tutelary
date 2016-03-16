from django.core.exceptions import ObjectDoesNotExist
from .exceptions import InvalidPermissionObjectException
from .models import PermissionSet
from .engine import Action, Object


class Backend:
    """Custom authentication backend: dispatches ``has_perm`` queries to
    the user's permission set.

    """
    def _get_pset(self, user):
        try:
            if user.is_authenticated():
                return user.permissionset.first().tree()
            else:
                return PermissionSet.objects.get(anonymous_user=True).tree()
        except AttributeError:
            raise ObjectDoesNotExist

    @staticmethod
    def _obj_ok(obj):
        return obj is None or callable(obj) or isinstance(obj, Object)

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
            if not self._obj_ok(obj):
                if hasattr(obj, 'get_permissions_object'):
                    obj = obj.get_permissions_object(perm)
                else:
                    raise InvalidPermissionObjectException
            return self._get_pset(user).allow(Action(perm), obj)
        except ObjectDoesNotExist:
            return False

    def permitted_actions(self, user, obj=None):
        """Determine list of permitted actions for an object or object
        pattern.

        :param user: The user to test.
        :type user: ``User``
        :param obj: A function mapping from action names to object
                    paths to test.
        :type obj: callable
        :returns: ``list(tutelary.engine.Action)`` -- permitted actions.

        """
        try:
            if not self._obj_ok(obj):
                raise InvalidPermissionObjectException
            return self._get_pset(user).permitted_actions(obj)
        except ObjectDoesNotExist:
            return []
