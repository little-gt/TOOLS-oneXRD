# Import the plugin's UI and analysis logic
from .ui import MicrostructureWindow
from . import analysis as an


class MicrostructureRunner:
    """The logic controller for the microstructure plugin."""

    def __init__(self, api):
        self.api = api
        self.ui = None  # UI window will be assigned after creation

    def run_scherrer(self, peak_index):
        try:
            exp_data = self.api.get_experimental_data()
            peak_info = exp_data.peaks_df.iloc[peak_index]

            size = an.calculate_scherrer_size(
                peak_fwhm=peak_info['fwhm_angle'],
                peak_angle=peak_info['angle']
            )
            self.ui.show_scherrer_result(f"Result: {size:.2f} Å")
        except Exception as e:
            self.api.log(f"Scherrer calculation failed: {e}", level='error')
            self.ui.show_scherrer_result(f"Error: {e}")

    def run_williamson_hall(self):
        try:
            exp_data = self.api.get_experimental_data()
            results = an.calculate_williamson_hall(exp_data.peaks_df)

            self.ui.display_wh_plot(results)
            self.ui.update_wh_results(
                results['crystallite_size_A'],
                results['strain'],
                results['r_squared']
            )
        except Exception as e:
            self.api.log(f"W-H calculation failed: {e}", level='error')
            # Optionally, clear the plot and show error on UI


def launch_plugin(api):
    """The main launch function for the plugin."""
    exp_data = api.get_experimental_data()
    if exp_data is None or exp_data.peaks_df.empty:
        api.log("Cannot launch Microstructure Analysis: No peaks found.", level='warning')
        from tkinter import messagebox
        messagebox.showwarning("Analysis Error", "Please find peaks before running microstructure analysis.",
                               parent=api.get_main_window())
        return

    main_window = api.get_main_window()
    runner = MicrostructureRunner(api)
    ui = MicrostructureWindow(main_window, runner, exp_data.peaks_df)
    runner.ui = ui  # Complete the two-way link


def register_plugin(api):
    """The required entry point for the plugin."""
    api.add_menu_item(
        menu_name="Analysis",
        action_name="Microstructure...",
        callback_function=lambda: launch_plugin(api)
    )