import os
import pandas as pd

# Import the UI we created for this plugin
from .ui import BatchWindow

# Import necessary components from the main oneXRD application
# This demonstrates the power of reusing our core, stable code
from oneXRD.importers import load_data, DataImportError
from oneXRD.analysis import background as bg_analysis
from oneXRD.analysis import peak_finding as pk_analysis


class BatchRunner:
    """
    Contains the logic for running the batch process.
    This separates the complex logic from the UI.
    """

    def __init__(self, api):
        self.api = api
        self.ui = None  # The UI window will be assigned after creation

    def run_batch(self, params):
        """The main batch processing logic."""
        try:
            input_folder = params['input_folder']
            output_name = params['output_name']

            # Get a list of valid files to process
            all_files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
            total_files = len(all_files)
            if total_files == 0:
                self.ui.log_message("No files found in the selected folder.", "warning")
                self.ui.on_batch_complete()
                return

            all_results = []

            for i, filename in enumerate(all_files):
                filepath = os.path.join(input_folder, filename)
                self.ui.log_message(f"Processing '{filename}' ({i + 1}/{total_files})...")
                self.ui.set_progress((i + 1) / total_files)

                try:
                    # 1. Load Data
                    angles, intensities = load_data(filepath)

                    # 2. Background Subtraction (if enabled)
                    if params['do_background']:
                        intensities = intensities - bg_analysis.subtract_iterative_erosion(
                            intensities, iterations=params['bg_iterations']
                        )

                    # 3. Peak Finding (if enabled)
                    if params['do_peaks']:
                        peaks_df = pk_analysis.find_all_peaks(
                            angles, intensities, min_prominence=params.get('pk_prominence')
                        )
                        # For this example, we'll just record the strongest peak
                        if not peaks_df.empty:
                            strongest_peak = peaks_df.sort_values(by='intensity', ascending=False).iloc[0]
                            all_results.append({
                                'filename': filename,
                                'strongest_peak_angle': strongest_peak['angle'],
                                'strongest_peak_intensity': strongest_peak['intensity'],
                                'strongest_peak_fwhm': strongest_peak['fwhm_angle']
                            })
                        else:
                            all_results.append({'filename': filename, 'strongest_peak_angle': 'N/A'})

                except (DataImportError, Exception) as e:
                    self.ui.log_message(f"Could not process '{filename}'. Error: {e}", "error")
                    all_results.append({'filename': filename, 'strongest_peak_angle': 'ERROR'})

            # --- Save Results ---
            results_df = pd.DataFrame(all_results)
            output_path = os.path.join(input_folder, output_name)
            results_df.to_csv(output_path, index=False)
            self.ui.log_message(f"Results saved to '{output_path}'", "success")

        except Exception as e:
            self.ui.log_message(f"A critical error occurred: {e}", "error")
        finally:
            self.ui.on_batch_complete()


def launch_batch_processor(api):
    """The function that is called by the menu item to open the plugin window."""
    main_window = api.get_main_window()

    # The runner contains the logic
    runner = BatchRunner(api)

    # The window is the UI, and it gets a reference to the runner
    batch_window = BatchWindow(main_window, runner)

    # The runner gets a reference to the UI so it can send feedback
    runner.ui = batch_window


def register_plugin(api):
    """
    The required entry point for the plugin.
    oneXRD calls this function and passes the PluginAPI object.
    """
    api.add_menu_item(
        menu_name="Tools",
        action_name="Batch Processing...",
        callback_function=lambda: launch_batch_processor(api)
    )

