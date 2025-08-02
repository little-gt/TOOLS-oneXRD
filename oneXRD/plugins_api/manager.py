import os
import importlib
from .api import PluginAPI


class PluginManager:
    """
    Discovers, loads, and manages all available plugins.
    """

    def __init__(self, main_window, project_manager):
        """
        Initializes the PluginManager.

        Args:
            main_window: A reference to the application's main window.
            project_manager: A reference to the application's project manager.
        """
        self.api = PluginAPI(main_window, project_manager)
        self.loaded_plugins = {}

    def discover_and_load_plugins(self, plugin_dir='plugins'):
        """
        Scans a directory for valid plugins, imports them, and calls their
        registration function.

        A valid plugin is a subdirectory containing an `__init__.py` file
        which has a `register_plugin(api)` function.

        Args:
            plugin_dir (str, optional): The directory to scan for plugins.
                                        Defaults to 'plugins'.
        """
        if not os.path.isdir(plugin_dir):
            print(f"WARNING: Plugin directory '{plugin_dir}' not found. Skipping plugin loading.")
            return

        for plugin_name in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, plugin_name)

            # A valid plugin must be a directory containing an __init__.py
            if not os.path.isdir(plugin_path) or not os.path.exists(os.path.join(plugin_path, '__init__.py')):
                continue

            try:
                # Dynamically import the plugin module (e.g., 'plugins.my_plugin')
                module_path = f"{plugin_dir}.{plugin_name}"
                plugin_module = importlib.import_module(module_path)

                # A valid plugin module must have a 'register_plugin' function
                if hasattr(plugin_module, 'register_plugin') and callable(plugin_module.register_plugin):
                    print(f"INFO: Registering plugin '{plugin_name}'...")
                    # Call the plugin's registration function, passing the API
                    plugin_module.register_plugin(self.api)
                    self.loaded_plugins[plugin_name] = plugin_module
                    print(f"INFO: Successfully registered '{plugin_name}'.")
                else:
                    print(f"WARNING: Plugin '{plugin_name}' is invalid: missing 'register_plugin' function.")

            except Exception as e:
                # Catch any error during import or registration to prevent one bad plugin from crashing the app
                print(f"ERROR: Could not load plugin '{plugin_name}'. Reason: {e}")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    import shutil


    # --- Mock the necessary application components ---
    class MockMainWindow:
        def add_plugin_menu_item(self, menu, action, func):
            print(f"MockUI: Plugin added menu item '{action}' to '{menu}'.")


    class MockProject:
        pass


    print("--- Testing PluginManager ---")

    # --- 1. Create a temporary file structure for testing plugins ---
    TEST_PLUGIN_DIR = "temp_test_plugins"
    VALID_PLUGIN_PATH = os.path.join(TEST_PLUGIN_DIR, "valid_plugin")
    BROKEN_PLUGIN_PATH = os.path.join(TEST_PLUGIN_DIR, "broken_plugin")
    INVALID_PLUGIN_PATH = os.path.join(TEST_PLUGIN_DIR, "invalid_plugin")

    # Clean up previous runs if they exist
    if os.path.exists(TEST_PLUGIN_DIR):
        shutil.rmtree(TEST_PLUGIN_DIR)

    os.makedirs(VALID_PLUGIN_PATH)
    os.makedirs(BROKEN_PLUGIN_PATH)
    os.makedirs(INVALID_PLUGIN_PATH)

    # --- 2. Write the Python code for the mock plugins ---

    # This is a good plugin
    with open(os.path.join(VALID_PLUGIN_PATH, "__init__.py"), "w") as f:
        f.write("""
def register_plugin(api):
    print("  --> Valid plugin registered!")
    api.add_menu_item('Plugins', 'My Valid Action', lambda: print('Action called!'))
""")

    # This plugin will raise an error during registration
    with open(os.path.join(BROKEN_PLUGIN_PATH, "__init__.py"), "w") as f:
        f.write("""
def register_plugin(api):
    print("  --> Broken plugin trying to register...")
    raise ValueError("This plugin is intentionally broken.")
""")

    # This plugin is invalid because it's missing the registration function
    with open(os.path.join(INVALID_PLUGIN_PATH, "__init__.py"), "w") as f:
        f.write("""
def some_other_function():
    pass
""")

    # --- 3. Setup and run the PluginManager ---
    print("\n[Test] Discovering and loading plugins...")

    mock_window = MockMainWindow()
    mock_project = MockProject()

    # The manager needs to know where to look for the 'temp_test_plugins' package
    # We add the current directory to the path temporarily
    import sys

    sys.path.insert(0, os.getcwd())

    manager = PluginManager(mock_window, mock_project)
    manager.discover_and_load_plugins(plugin_dir=TEST_PLUGIN_DIR)

    # --- 4. Assert the results ---
    print("\nVerifying results...")
    assert 'valid_plugin' in manager.loaded_plugins
    assert 'broken_plugin' not in manager.loaded_plugins
    assert 'invalid_plugin' not in manager.loaded_plugins
    print("  --> SUCCESS: Correctly loaded valid plugin and ignored others.")

    # --- 5. Cleanup ---
    print("\nCleaning up test directory...")
    shutil.rmtree(TEST_PLUGIN_DIR)
    # Remove the path we added
    sys.path.pop(0)
    print("Cleanup complete.")
