import os

CONFIG_FILE = "config.ini"

def get_config_path():
    # Go one directory up from where `config_utils.py` is located
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        CONFIG_FILE
    )

