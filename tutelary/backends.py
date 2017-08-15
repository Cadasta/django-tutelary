from django.core.exceptions import ObjectDoesNotExist
from .exceptions import InvalidPermissionObjectException
from .engine import Action, Object


class Backend:
    """Custom authentication backend: dispatches ``has_perm`` queries to
    the user's permission set.

    """
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
            return user.permset_tree.allow(Action(perm), obj)
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
            return user.permset_tree.permitted_actions(obj)
        except ObjectDoesNotExist:
            return []
