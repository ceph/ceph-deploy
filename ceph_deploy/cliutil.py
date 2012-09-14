def priority(num):
    """
    Decorator to add a `priority` attribute to the function.
    """
    def add_priority(fn):
        fn.priority = num
        return fn
    return add_priority
