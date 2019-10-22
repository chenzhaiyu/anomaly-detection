# -*- coding: utf-8 -*-


class GlobalManager:
    """
    manage all the global variables across the modules
    """

    def __init__(self):
        global _global_dict
        _global_dict = {}

    @staticmethod
    def set_value(name, value):
        """
        set value in a dict, using its name as key
        :param name: variable name
        :param value: variable value
        :return: None
        """
        _global_dict[name] = value

    @staticmethod
    def get_value(name, _default_value=None):
        """
        get value from a dict
        :param name: variable name
        :param _default_value: default variable value
        :return: value corresponding to the input name
        """
        try:
            return _global_dict[name]
        except KeyError:
            return _default_value


global_manager = GlobalManager()
