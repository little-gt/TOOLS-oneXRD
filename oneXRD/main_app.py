import os
import customtkinter as ctk
from tkinter import filedialog, simpledialog
from tkinter import messagebox  # --- FIX 1: Import messagebox directly from tkinter ---

# Import all our major application components
from .ui.main_window import MainWindow
from .core.project import Project
from .core.database import DatabaseManager
from .core.xrd_data import XRDData
from .plugins_api.manager import PluginManager

# Import the backend modules
from .importers import load_data, DataImportError
from .analysis import background as bg_analysis
from .analysis import peak_finding as pk_analysis
from .analysis import fitting as ft_analysis
from .analysis import search_match as sm_analysis
from .analysis.background import BackgroundError
from .analysis.peak_finding import PeakFindingError


class MainApplication:
    """
    The main controller class for the oneXRD application.
    """

    def __init__(self):
        # --- 1. Initialize Data Models ---
        self.project = Project()
        self.db_manager = DatabaseManager(db_path="oneXRD_projects.db")

        # --- 2. Initialize the View (UI) ---
        self.view = MainWindow(controller=self)

        # --- 3. Initialize the Plugin System ---
        self.plugin_manager = PluginManager(main_window=self.view, project_manager=self.project)
        self.plugin_manager.discover_and_load_plugins()

        # --- 4. Final UI Setup ---
        self.refresh_db_list()
        self.view.refresh_ui(self.project)
        self.view.update_status("Ready. Please open a file or load a project from the database.")

    def run(self):
        """Starts the main application event loop."""
        self.view.mainloop()

    # --- File Menu Callbacks ---
    def open_file(self):
        filetypes = [
            ("All XRD Files", "*.raw *.xrdml *.xy *.csv *.txt *.dat *.cif"),
            ("Experimental Data", "*.raw *.xrdml *.xy *.csv *.txt *.dat"),
            ("CIF Reference", "*.cif"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(title="Open File", filetypes=filetypes)
        if not filepath:
            return

        try:
            self.view.update_status(f"Loading {os.path.basename(filepath)}...")
            angles, intensities = load_data(filepath)

            is_ref = filepath.lower().endswith('.cif')
            xrd_data = XRDData(angles, intensities, filename=filepath, is_reference=is_ref)

            if is_ref:
                # --- MODIFIED LOGIC ---
                self.project.add_reference(xrd_data)
                self.view.update_status(f"Added reference: {xrd_data.display_name}")
                # If we have experimental data, refresh to show the overlay.
                # If not, the user knows they still need to open experimental data.
                if self.project.has_experimental_data:
                    self.view.refresh_ui(self.project)
                else:
                    self.view.show_error_message("Reference Loaded",
                                                 f"'{xrd_data.display_name}' was loaded as a reference. Please open an experimental data file to begin analysis.")
            else:
                self.project.clear_project()
                self.project.load_experimental_data(xrd_data)
                self.view.update_status(f"Loaded new experiment: {xrd_data.display_name}")
                # Refresh UI now that we have experimental data
                self.view.refresh_ui(self.project)

        except DataImportError as e:
            self.view.show_error_message("File Load Error", str(e))
            self.view.update_status("File loading failed.")

    # --- Analysis Callbacks ---
    def apply_background(self):
        if not self.project.has_experimental_data: return
        params = self.view.analysis_frame.get_bg_params()
        if params is None: return
        xrd_data = self.project.experimental_data
        try:
            if params['method'] == 'Polynomial':
                self.view.show_error_message("Not Implemented",
                                             "Polynomial background requires interactive point selection, which is not yet implemented.")
                return
            elif params['method'] == 'Iterative Erosion':
                bg_curve = bg_analysis.subtract_iterative_erosion(xrd_data.raw_intensities,
                                                                  iterations=params.get('iterations', 50))
            xrd_data.set_background(bg_curve)
            self.view.refresh_ui(self.project)
            self.view.update_status("Background subtracted.")
        except BackgroundError as e:
            self.view.show_error_message("Background Error", str(e))

    def clear_background(self):
        if not self.project.has_experimental_data: return
        self.project.experimental_data.reset_processing()
        self.view.refresh_ui(self.project)
        self.view.update_status("Processing reset.")

    def find_peaks(self):
        if not self.project.has_experimental_data: return
        params = self.view.analysis_frame.get_peak_params()
        if params is None: return
        xrd_data = self.project.experimental_data
        try:
            peaks_df = pk_analysis.find_all_peaks(xrd_data.processed_angles, xrd_data.processed_intensities, **params)
            xrd_data.set_peaks(peaks_df)
            self.view.refresh_ui(self.project)
            self.view.update_status(f"Found {len(peaks_df)} peaks.")
        except PeakFindingError as e:
            self.view.show_error_message("Peak Finding Error", str(e))

    # --- Database Callbacks ---
    def save_project(self):
        if not self.project.has_experimental_data: return
        sample_name = simpledialog.askstring("Save Project", "Enter a name for this sample:", parent=self.view)
        if not sample_name: return
        try:
            exp_id = self.db_manager.add_experiment(
                sample_name=sample_name,
                angles=self.project.experimental_data.raw_angles,
                intensities=self.project.experimental_data.raw_intensities
            )
            self.project.db_id = exp_id
            self.refresh_db_list()
            self.view.update_status(f"Project '{sample_name}' saved with ID {exp_id}.")
        except Exception as e:
            self.view.show_error_message("Database Error", f"Failed to save project: {e}")

    def load_from_db(self, exp_id):
        try:
            data_dict = self.db_manager.get_experiment_data(exp_id)
            xrd_data = XRDData(data_dict['angles'], data_dict['intensities'], filename=data_dict['sample_name'])
            self.project.clear_project()
            self.project.load_experimental_data(xrd_data, db_id=exp_id)
            self.view.refresh_ui(self.project)
            self.view.update_status(f"Loaded project '{xrd_data.display_name}' from database.")
        except Exception as e:
            self.view.show_error_message("Database Error", f"Failed to load project: {e}")

    def delete_from_db(self, exp_id):
        try:
            self.db_manager.delete_experiment(exp_id)
            self.refresh_db_list()
            self.view.update_status(f"Deleted project ID {exp_id} from database.")
        except Exception as e:
            self.view.show_error_message("Database Error", f"Failed to delete project: {e}")

    def refresh_db_list(self):
        try:
            experiments = self.db_manager.get_all_experiments_summary()
            self.view.database_frame.update_experiment_list(experiments)
        except Exception as e:
            self.view.show_error_message("Database Error", f"Could not refresh experiment list: {e}")

    # --- Help Menu Callbacks ---
    def show_about_dialog(self):
        # --- FIX 2: Call messagebox directly, not as an attribute of ctk ---
        messagebox.showinfo(
            "About oneXRD",
            "oneXRD - A modular XRD analysis software.\n\n"
            "Developed with passion and collaboration.\n\n"
            "Version: 0.1.3 (MVP)",
            parent=self.view
        )


# =============================================================================
# Standalone Execution
# =============================================================================
if __name__ == '__main__':
    app = MainApplication()
    app.run()
