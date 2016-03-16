class TutelaryException(Exception):
    pass


class EffectException(TutelaryException):
    """Exception raised when an effect type other that ``allow`` or
    ``deny`` is encountered in a JSON policy body.

    """
    def __init__(self, effect):
        super().__init__("illegal permission effect: '" + effect + "'")


class PatternOverlapException(TutelaryException):
    """Exception raised when overlapping action or object patterns are
    used in a single policy clause.

    """
    def __init__(self, exc_type):
        super().__init__(
            "overlapping " + exc_type + " patterns in policy clause"
        )


class PolicyBodyException(TutelaryException):
    """Exception raised for miscellaneous errors in JSON policy bodies."""
    def __init__(self, msg=None, lineno=None, colno=None):
        if msg is not None:
            super().__init__("illegal policy body: " + msg)
        else:
            super().__init__(
                "illegal policy body: " +
                "line " + str(lineno) + ", column " + str(colno)
            )


class VariableSubstitutionException(TutelaryException):
    """Exception raised for illegal variable substitutions when using JSON
    policy bodies.

    """
    def __init__(self):
        super().__init__("illegal variable substitution in policy body")


class RoleVariableException(TutelaryException):
    """Exception raised for missing or illegal variable substitutions for
    permissions roles.

    """
    def __init__(self, msg):
        super().__init__("illegal role variables: " + msg)


class DecoratorException(TutelaryException):
    """Exception raised if the ``permissioned_model`` decorator is used
    without the required ``TutelaryMeta`` class member being included
    in the model.

    """
    def __init__(self, decorator, msg):
        super().__init__(
            "error expanding decorator '" + decorator + "': " + msg
        )


class PermissionObjectException(TutelaryException):
    """Exception raised by the ``permissioned_model`` decorator if a
    ``permissions_object`` property in the ``actions`` list refers to
    a non-existent model field, or to a field that is not a foreign
    key or one-to-one relation field.

    """
    def __init__(self, prop):
        super().__init__(
            "invalid permissions_object property '" + prop +
            "' in permissioned_model"
        )


class InvalidPermissionObjectException(TutelaryException):
    """Exception raised by authentication backend if the object passed to
    backend methods is not either a ``tutelary.engine.Object`` or a
    Django model instance with a ``get_permissions_object`` method.

    """
    def __init__(self):
        super().__init__("invalid object passed to django-tutelary " +
                         "backend method")
