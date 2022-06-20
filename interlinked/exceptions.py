class InterlinkedException(Exception):
    pass

class NoRootException(InterlinkedException):
    pass

class LoopException(InterlinkedException):
    pass

class UnknownDependency(InterlinkedException):
    pass
