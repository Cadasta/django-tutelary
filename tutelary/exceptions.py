class IllegalEffectException(Exception):
    def __init__(self, effect):
        super().__init__("illegal permission effect: '" + effect + "'")


class IllegalPatternOverlapException(Exception):
    def __init__(self, type):
        super().__init__("overlapping " + type + " patterns in policy clause")
