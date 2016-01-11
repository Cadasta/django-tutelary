class TutelaryException(Exception):
    pass


class EffectException(TutelaryException):
    def __init__(self, effect):
        super(EffectException, self).__init__(
            "illegal permission effect: '" + effect + "'"
        )


class PatternOverlapException(TutelaryException):
    def __init__(self, exc_type):
        super(PatternOverlapException, self).__init__(
            "overlapping " + exc_type + " patterns in policy clause"
        )


class PolicyBodyException(TutelaryException):
    def __init__(self, msg=None, lineno=None, colno=None):
        if msg is not None:
            super(PolicyBodyException, self).__init__(
                "illegal policy body: " + msg
            )
        elif lineno is not None:
            super(PolicyBodyException, self).__init__(
                "illegal policy body: " +
                "line " + str(lineno) + ", column " + str(colno)
            )
        else:
            super(PolicyBodyException, self).__init__(
                "illegal policy body"
            )


class VariableSubstitutionException(TutelaryException):
    def __init__(self):
        super(VariableSubstitutionException, self).__init__(
            "illegal variable substitution in policy body"
        )


class DecoratorException(TutelaryException):
    def __init__(self, decorator, msg):
        super(DecoratorException, self).__init__(
            "error expanding decorator '" + decorator + "': " + msg
        )
