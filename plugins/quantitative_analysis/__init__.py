import matplotlib.pyplot as plt  # Import for color mapping
from tkinter import messagebox
from .ui import QpaWindow
from .analysis import calculate_rir_quantification, QpaError


class QpaRunner:
    """The logic controller for the QPA plugin."""

    def __init__(self, api):
        self.api = api
        self.ui = None

    def run_calculation(self, phase_data):
        """Calls the analysis function and tells the UI to update with rich data."""
        if not self.ui: return

        try:
            # phase_data is now a list of dicts with names, angles, intensities, rir
            percentages = calculate_rir_quantification(phase_data)

            # Combine results into a single structure for the UI
            for i, p_data in enumerate(phase_data):
                p_data['wt_percent'] = percentages[i]

            self.ui.update_results(phase_data)
            self.api.log("QPA calculation complete.", level="info")

        except QpaError as e:
            self.api.log(f"QPA Error: {e}", level="error")
            messagebox.showerror("Calculation Error", str(e), parent=self.ui)


def launch_qpa(api):
    """The main launch function for the QPA plugin."""
    project = api.get_project()
    if not project.has_experimental_data or project.experimental_data.peaks_df.empty:
        api.log("Please find peaks before launching Quantitative Analysis.", level="warning")
        messagebox.showwarning("Prerequisite Missing", "Please run 'Find Peaks' first.", parent=api.get_main_window())
        return

    main_window = api.get_main_window()
    runner = QpaRunner(api)
    # The UI now needs the full experimental data object for plotting
    ui_window = QpaWindow(main_window, runner, project.experimental_data)
    runner.ui = ui_window


def register_plugin(api):
    """The required entry point for the plugin."""
    api.add_menu_item(
        menu_name="Analysis",
        action_name="Quantitative Analysis (RIR)...",
        callback_function=lambda: launch_qpa(api)
    )