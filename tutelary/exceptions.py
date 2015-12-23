class EffectException(Exception):
    def __init__(self, effect):
        super().__init__("illegal permission effect: '" + effect + "'")


class PatternOverlapException(Exception):
    def __init__(self, type):
        super().__init__("overlapping " + type + " patterns in policy clause")


class PolicyBodyException(Exception):
    def __init__(self, msg=None, lineno=None, colno=None):
        if msg is not None:
            super().__init__("illegal policy body: " + msg)
        elif lineno is not None:
            super().__init__("illegal policy body: " +
                             "line " + str(lineno) + ", column " + str(colno))
        else:
            super().__init__("illegal policy body")


class VariableSubstitutionException(Exception):
    def __init__(self):
        super().__init__("illegal variable substitution in policy body")
