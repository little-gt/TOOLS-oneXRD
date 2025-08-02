import customtkinter as ctk
from tkinter import Menu

# Import all our custom frames
from .frames.plot_frame import PlotFrame
from .frames.analysis_frame import AnalysisFrame
from .frames.database_frame import DatabaseFrame
from .frames.peak_list_frame import PeakListFrame


class MainWindow(ctk.CTk):
    """
    The main application window that assembles all other UI components.
    Acts as the main 'View' in the MVC architecture.
    """

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        self.title("oneXRD - XRD Analysis Software")
        self.geometry("1400x850")

        # --- Configure the main window grid ---
        self.grid_columnconfigure(1, weight=1)  # Main content area resizes
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self._create_menubar()

    def _create_widgets(self):
        """Create and place all the main frames."""
        # --- Left Side Panel ---
        self.left_panel = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")
        self.left_panel.grid_rowconfigure(1, weight=1)  # Make DB frame expand

        self.analysis_frame = AnalysisFrame(self.left_panel, self.controller)
        self.analysis_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.database_frame = DatabaseFrame(self.left_panel, self.controller)
        self.database_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # --- Main Content Area ---
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content.grid_rowconfigure(0, weight=3)  # Plot takes more space
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        self.plot_frame = PlotFrame(self.main_content, self.controller)
        self.plot_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        self.peak_list_frame = PeakListFrame(self.main_content, self.controller)
        self.peak_list_frame.grid(row=1, column=0, sticky="nsew")

        # --- Status Bar ---
        self.status_bar = ctk.CTkLabel(self, text="Welcome to oneXRD!", anchor="w")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 5))

    def _create_menubar(self):
        """Creates the main application menubar."""
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        # File Menu
        file_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File...", command=self.controller.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Help Menu
        help_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.controller.show_about_dialog)

        # Plugins Menu (will be populated dynamically)
        self.plugin_menus = {}  # To hold references to plugin submenus

    def add_plugin_menu_item(self, menu_name, action_name, callback):
        """Allows plugins to add items to the menubar."""
        if menu_name not in self.plugin_menus:
            plugin_menu = Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label=menu_name, menu=plugin_menu)
            self.plugin_menus[menu_name] = plugin_menu

        self.plugin_menus[menu_name].add_command(label=action_name, command=callback)

    def update_status(self, message):
        """Updates the text in the status bar."""
        self.status_bar.configure(text=message)

    def show_error_message(self, title, message):
        """Displays a modal error dialog."""
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self)

    def refresh_ui(self, project):
        """Refreshes all UI components based on the project state."""
        has_data = project.has_experimental_data

        # Update plot
        if has_data:
            # --- MODIFIED: Pass the list of references to the plot frame ---
            reference_list = list(project.reference_data.values())
            self.plot_frame.plot_data(project.experimental_data, reference_list)
        else:
            self.plot_frame.clear_plot()

        # Update peak list
        self.peak_list_frame.update_peak_list(project.experimental_data.peaks_df if has_data else None)

        # Update analysis controls
        self.analysis_frame.update_view_state(has_data)

        # Update database controls
        self.database_frame.update_view_state(has_data)


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    class MockController:
        """A mock controller to test the MainWindow in isolation."""

        def __init__(self, view):
            self.view = view
            print("MockController initialized.")

        def open_file(self): print("Controller: Open File called")

        def save_project(self): print("Controller: Save Project called")

        def load_from_db(self, exp_id): print(f"Controller: Load from DB called with ID: {exp_id}")

        def delete_from_db(self, exp_id): print(f"Controller: Delete from DB called with ID: {exp_id}")

        def apply_background(self): print("Controller: Apply Background called")

        def clear_background(self): print("Controller: Clear Background called")

        def find_peaks(self): print("Controller: Find Peaks called")

        def show_about_dialog(self): print("Controller: Show About Dialog called")

        def show_error(self, title, msg): self.view.show_error_message(title, msg)


    # To test the UI, we just need to initialize and run the main window.
    # The controller is mocked, so no logic will execute, but we can see the full layout.
    print("Initializing MainWindow for visual testing...")


    # Need to create a dummy project for the refresh call to work
    class MockProject:
        has_experimental_data = False


    controller_instance = MockController(None)
    main_app_window = MainWindow(controller_instance)
    controller_instance.view = main_app_window  # Link view back to controller

    # Simulate a refresh to set the initial state
    main_app_window.refresh_ui(MockProject())

    main_app_window.mainloop()
