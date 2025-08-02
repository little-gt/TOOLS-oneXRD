import customtkinter as ctk
import pandas as pd
import numpy as np

# Matplotlib imports for embedding the plot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# We need our XRDData class for type hinting and testing
# This assumes the script is run from the project root or the package is installed
try:
    from oneXRD.core.xrd_data import XRDData
except ImportError:
    # Fallback for standalone testing
    class XRDData:  # A minimal mock for standalone execution
        def __init__(self, raw_angles, raw_intensities, filename=None, is_reference=False):
            self.filename, self.is_reference = filename, is_reference
            self.raw_angles, self.raw_intensities = raw_angles, raw_intensities
            self.processed_intensities, self.background_curve, self.peaks_df = raw_intensities, None, pd.DataFrame()


class PlotFrame(ctk.CTkFrame):
    """
    A frame dedicated to displaying the XRD pattern using Matplotlib.
    """

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        # --- Matplotlib Figure and Canvas ---
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # --- Matplotlib Toolbar ---
        toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        toolbar_frame.pack(side="bottom", fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.format_plot()

    def format_plot(self):
        """Applies standard formatting to the plot."""
        self.ax.set_xlabel("Angle (2θ)")
        self.ax.set_ylabel("Intensity (a.u.)")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.figure.tight_layout()

    def clear_plot(self):
        """Clears all data from the plot."""
        self.ax.clear()
        self.format_plot()
        self.canvas.draw()

    def plot_data(self, xrd_data_obj, reference_list=None):
        """
        Plots all relevant data from an XRDData object and any references.

        Args:
            xrd_data_obj (XRDData): The main experimental data to plot.
            reference_list (list[XRDData], optional): A list of reference patterns
                                                      to overlay.
        """
        self.ax.clear()

        # Plot the main intensity data
        self.ax.plot(xrd_data_obj.processed_angles, xrd_data_obj.processed_intensities, label=xrd_data_obj.display_name)

        # Plot the background curve if it exists
        if xrd_data_obj.background_curve is not None:
            self.ax.plot(xrd_data_obj.raw_angles, xrd_data_obj.background_curve, 'r--', label="Background")

        # Plot markers for found peaks if they exist
        if not xrd_data_obj.peaks_df.empty:
            self.ax.plot(xrd_data_obj.peaks_df['angle'], xrd_data_obj.peaks_df['intensity'], 'kx', markersize=8,
                         label="Peaks")

        # --- NEW: Plot all references ---
        if reference_list:
            max_intensity = self.ax.get_ylim()[1]
            for ref_data in reference_list:
                # Use vertical lines for reference peaks for clarity
                scaled_intensities = (ref_data.raw_intensities / 100.0) * max_intensity * 0.5
                self.ax.vlines(ref_data.raw_angles, 0, scaled_intensities, color='green', alpha=0.7,
                               label=ref_data.display_name)

        self.format_plot()
        self.ax.legend()
        self.canvas.draw()

    def plot_reference_data(self, ref_data_obj, offset=0):
        """Overlays a reference pattern on the existing plot."""
        # Use vertical lines for reference peaks for clarity
        max_intensity = self.ax.get_ylim()[1]
        scaled_intensities = (ref_data_obj.raw_intensities / 100.0) * max_intensity * 0.5  # Scale to 50% of plot height

        self.ax.vlines(ref_data_obj.raw_angles, offset, scaled_intensities + offset, color='green',
                       label=ref_data_obj.display_name)

        self.format_plot()
        self.ax.legend()
        self.canvas.draw()


# =============================================================================
# Standalone Test Block
# =============================================================================
if __name__ == '__main__':
    class MockController:
        pass


    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("PlotFrame Test")
            self.geometry("800x700")

            # --- Main container ---
            main_container = ctk.CTkFrame(self)
            main_container.pack(side="right", fill="both", expand=True, padx=10, pady=10)

            self.controller = MockController()
            self.plot_frame = PlotFrame(main_container, self.controller)
            self.plot_frame.pack(fill="both", expand=True)

            # --- Control panel for testing ---
            control_panel = ctk.CTkFrame(self, width=200)
            control_panel.pack(side="left", fill="y", padx=10, pady=10)

            ctk.CTkButton(control_panel, text="Plot Raw Data", command=self.test_plot_raw).pack(pady=5, padx=10,
                                                                                                fill="x")
            ctk.CTkButton(control_panel, text="Plot Processed Data", command=self.test_plot_processed).pack(pady=5,
                                                                                                            padx=10,
                                                                                                            fill="x")
            ctk.CTkButton(control_panel, text="Add Reference", command=self.test_add_reference).pack(pady=5, padx=10,
                                                                                                     fill="x")
            ctk.CTkButton(control_panel, text="Clear Plot", command=self.plot_frame.clear_plot).pack(pady=5, padx=10,
                                                                                                     fill="x")

            self._prepare_test_data()

        def _prepare_test_data(self):
            """Creates dummy XRDData objects for testing."""
            # 1. Raw Data
            angles = np.linspace(10, 80, 1000)
            true_bg = 100 + 50 * np.sin((angles - 10) / 20)
            peak1 = 800 * np.exp(-((angles - 30) ** 2) / (2 * 0.5 ** 2))
            peak2 = 500 * np.exp(-((angles - 55) ** 2) / (2 * 0.8 ** 2))
            intensities = true_bg + peak1 + peak2
            self.raw_xrd_data = XRDData(angles, intensities, "raw_data.xy")

            # 2. Processed Data
            self.processed_xrd_data = XRDData(angles, intensities, "processed_data.xy")
            self.processed_xrd_data.background_curve = true_bg
            self.processed_xrd_data.processed_intensities = intensities - true_bg
            peaks = pd.DataFrame({'angle': [30.0, 55.0], 'intensity': [800.0, 500.0]})
            self.processed_xrd_data.peaks_df = peaks

            # 3. Reference Data
            ref_angles = np.array([30.1, 42.5, 55.2, 68.0])
            ref_intensities = np.array([100, 40, 80, 20])
            self.ref_xrd_data = XRDData(ref_angles, ref_intensities, "NaCl.cif", is_reference=True)

        def test_plot_raw(self):
            print("Testing: Plotting raw data...")
            self.plot_frame.plot_data(self.raw_xrd_data)

        def test_plot_processed(self):
            print("Testing: Plotting processed data with background and peaks...")
            self.plot_frame.plot_data(self.processed_xrd_data)

        def test_add_reference(self):
            print("Testing: Overlaying reference pattern...")
            # We plot processed first to have something to overlay on
            self.test_plot_processed()
            self.plot_frame.plot_reference_data(self.ref_xrd_data)


    app = App()
    app.mainloop()
