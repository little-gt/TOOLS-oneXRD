# =============================================================================
# This file is the entry point for the Rietveld Refinement plugin.
# It registers the plugin with the main application and provides the function
# to launch the plugin's user interface.
# =============================================================================

from tkinter import messagebox

# Import the UI and Engine components of our plugin
from .ui import RietveldWindow
from .engine import RietveldEngine, RietveldError


def launch_refinement(api):
    """
    The main launch function for the Rietveld refinement plugin.
    It creates the engine and the UI window, handling any initialization errors.
    """
    main_window = api.get_main_window()

    try:
        # 1. Create an instance of the Rietveld engine.
        #    This will fail if GSAS-II is not installed.
        engine = RietveldEngine(api)

        # 2. Create the UI window, passing it the main window as its
        #    parent and the engine instance as its "runner".
        RietveldWindow(main_window, engine)

    except RietveldError as e:
        # 3. If the engine failed to initialize, show an error to the user.
        api.log(f"Failed to launch Rietveld plugin: {e}", level="error")
        messagebox.showerror(
            "Rietveld Plugin Error",
            f"Could not start the Rietveld refinement tool.\n\n"
            f"Reason: {e}\n\n"
            "Please ensure GSAS-II is correctly installed and accessible in your Python environment.",
            parent=main_window
        )


def register_plugin(api):
    """
    The required entry point for any oneXRD plugin.
    This function is called by the PluginManager at startup.

    Args:
        api (PluginAPI): The API object providing access to the main application.
    """
    api.add_menu_item(
        menu_name="Advanced",
        action_name="Rietveld Refinement...",
        # Use a lambda to pass the api object to our launcher function when clicked
        callback_function=lambda: launch_refinement(api)
    )