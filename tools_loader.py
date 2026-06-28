import pkgutil
import inspect
import importlib

from tool import Tool


def load_tools(package="tools") -> list[Tool]:
    tools = []

    package_module = importlib.import_module(package)

    for _, module_name, _ in pkgutil.walk_packages(
            package_module.__path__,
            package_module.__name__ + "."):

        module = importlib.import_module(module_name)

        for _, obj in inspect.getmembers(module, inspect.isclass):

            if (
                issubclass(obj, Tool)
                and obj is not Tool
                and getattr(obj, "enabled", True)
            ):
                tools.append(obj())

    return tools
