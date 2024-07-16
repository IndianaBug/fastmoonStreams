import yaml

def get_nested_variable_from_yaml(file_path, *keys):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        for key in keys:
            config = config.get(key, {})
        return config

def get_yaml_variable(file_path, what=None):
    config = get_nested_variable_from_yaml(file_path)
    if what:
        var = config.get(what, {})
        return var
    else:
        return config
