from importlib import import_module


def class_from_str(strategy_name):
    import_name = strategy_name.lower()
    class_name = "".join([s.capitalize() for s in strategy_name.split('_')])
    module = import_module('src.strategies.' + import_name)
    return getattr(module, class_name)


class SimulationType:
    """

    """

    def __init__(self, simulation):
        pass
