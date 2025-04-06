import os
import sys

CONFIG_FILE = "config.ini"

def get_config_path():
    """
    Get the appropriate config file path based on whether the application
    is running from source or as an installed executable.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # Use user's AppData directory on Windows
        app_data = os.getenv('APPDATA')
        if app_data:
            # Create OptimiseApp directory if it doesn't exist
            app_dir = os.path.join(app_data, 'OptimiseApp')
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, CONFIG_FILE)
        else:
            # Fallback to user's home directory
            home = os.path.expanduser('~')
            app_dir = os.path.join(home, '.OptimiseApp')
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, CONFIG_FILE)
    else:
        # Running from source
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            CONFIG_FILE
        )