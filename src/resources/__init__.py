import os

_RELATIVE_RESOURCE_PATH = "resources"


def get_resource_path(resource_name):
    current_directory_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_directory_path, _RELATIVE_RESOURCE_PATH, resource_name)
