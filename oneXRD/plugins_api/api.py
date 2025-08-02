import copy


class PluginAPI:
    """
    The API object passed to each plugin upon registration.

    This class provides a stable and safe interface for plugins to interact
    with the main application's data and UI components.
    """

    def __init__(self, main_window, project_manager):
        """
        Initializes the API for a specific plugin.

        Args:
            main_window: A reference to the application's main window instance.
            project_manager: A reference to the application's main project object.
        """
        self._main_window = main_window
        self._project = project_manager

    def get_main_window(self):
        """
        Returns a reference to the main application window.

        This is useful for parenting dialogs and other UI elements created by the plugin.

        Returns:
            QMainWindow: The main window instance.
        """
        return self._main_window

    def get_project(self):
        """
        Returns a deep copy of the entire current project object.

        This provides the plugin with all current data (experimental and reference)
        in a safe, read-only manner, preventing accidental modification of the
        main application's state.

        Returns:
            Project: A deep copy of the current project object.
        """
        return copy.deepcopy(self._project)

    def get_experimental_data(self):
        """
        A convenience method to get a deep copy of the current experimental data.

        Returns:
            XRDData or None: A deep copy of the experimental XRDData object,
                             or None if no data is loaded.
        """
        if self._project.has_experimental_data:
            return copy.deepcopy(self._project.experimental_data)
        return None

    def add_menu_item(self, menu_name, action_name, callback_function):
        """
        Adds a new action to a specified menu in the main window's menubar.

        Args:
            menu_name (str): The name of the menu to add to (e.g., 'Plugins').
            action_name (str): The text that will appear for this menu item.
            callback_function (callable): The function to be executed when the
                                          menu item is clicked.
        """
        self._main_window.add_plugin_menu_item(menu_name, action_name, callback_function)

    def log(self, message, level='info'):
        """
        Writes a message to the main application's log window.

        Args:
            message (str): The message to log.
            level (str, optional): The log level ('info', 'warning', 'error').
                                   Defaults to 'info'.
        """
        # In a real app, this would call a method on the main window's logger
        print(f"PLUGIN_LOG ({level.upper()}): {message}")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    # We need to create "mock" objects to simulate the main application

    class MockXRDData:
        def __init__(self, name):
            self.name = name


    class MockProject:
        def __init__(self):
            self.experimental_data = MockXRDData("exp_data")

        @property
        def has_experimental_data(self):
            return self.experimental_data is not None


    class MockMainWindow:
        def __init__(self):
            self.menu_items = {}

        def add_plugin_menu_item(self, menu, action, func):
            print(f"MockUI: Adding '{action}' to menu '{menu}'")
            if menu not in self.menu_items:
                self.menu_items[menu] = []
            self.menu_items[menu].append((action, func))


    class MockPlugin:
        def run_my_analysis(self):
            print("Plugin's analysis function was called!")


    print("--- Testing PluginAPI ---")

    # --- 1. Setup mock components ---
    mock_window = MockMainWindow()
    mock_project = MockProject()
    mock_plugin = MockPlugin()

    # --- 2. Initialize the API ---
    print("\n[Test 1] Initializing PluginAPI...")
    api = PluginAPI(mock_window, mock_project)
    assert api is not None
    print("  --> SUCCESS")

    # --- 3. Test data access methods ---
    print("\n[Test 2] Testing data access...")
    proj_copy = api.get_project()
    exp_data_copy = api.get_experimental_data()

    assert isinstance(proj_copy, MockProject)
    assert isinstance(exp_data_copy, MockXRDData)
    # Important: Test that it's a copy, not the original object
    assert proj_copy is not mock_project
    print("  --> SUCCESS: Correctly retrieved copies of project data.")

    # --- 4. Test UI interaction method ---
    print("\n[Test 3] Testing UI interaction...")
    api.add_menu_item(
        menu_name='Plugins',
        action_name='My Cool Analysis',
        callback_function=mock_plugin.run_my_analysis
    )

    assert 'Plugins' in mock_window.menu_items
    assert len(mock_window.menu_items['Plugins']) == 1
    action_name, func = mock_window.menu_items['Plugins'][0]
    assert action_name == 'My Cool Analysis'

    # Simulate clicking the menu item
    print("  Simulating menu click...")
    func()
    print("  --> SUCCESS: Menu item added and callback works.")

    # --- 5. Test logging method ---
    print("\n[Test 4] Testing logging...")
    api.log("This is a test message from a plugin.", level='info')
    api.log("Something might be wrong.", level='warning')
    print("  --> SUCCESS (Visual check of console output)")

