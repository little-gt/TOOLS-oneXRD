import customtkinter as ctk
import pandas as pd

# Matplotlib imports for embedding the plot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


class MicrostructureWindow(ctk.CTkToplevel):
    """The main UI window for the Microstructure Analysis plugin."""

    def __init__(self, master, runner, peaks_df):
        super().__init__(master)
        self.runner = runner
        self.title("Microstructure Analysis")
        self.geometry("700x650")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grab_set()

        # --- Create Tabbed Interface ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("Scherrer")
        self.tab_view.add("Williamson-Hall")

        self._create_scherrer_tab(self.tab_view.tab("Scherrer"), peaks_df)
        self._create_wh_tab(self.tab_view.tab("Williamson-Hall"))

    def _create_scherrer_tab(self, tab, peaks_df):
        """Creates all widgets for the Scherrer analysis tab."""
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="Scherrer Equation: Crystallite Size", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        peak_options = [f"{i}: Angle={row['angle']:.2f}, FWHM={row['fwhm_angle']:.4f}" for i, row in
                        peaks_df.iterrows()]
        self.scherrer_peak_combo = ctk.CTkComboBox(tab, values=peak_options)
        self.scherrer_peak_combo.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(tab, text="Calculate Size", command=self._on_scherrer_calculate).pack(pady=10)

        self.scherrer_result_label = ctk.CTkLabel(tab, text="Result: -", font=ctk.CTkFont(size=14))
        self.scherrer_result_label.pack(pady=10)

    def _create_wh_tab(self, tab):
        """Creates all widgets for the Williamson-Hall analysis tab."""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # --- Plot Frame ---
        plot_frame = ctk.CTkFrame(tab)
        plot_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)

        self.wh_figure = Figure(dpi=100)
        self.wh_ax = self.wh_figure.add_subplot(111)
        self.wh_canvas = FigureCanvasTkAgg(self.wh_figure, plot_frame)
        self.wh_canvas.get_tk_widget().pack(fill="both", expand=True)

        # --- Results and Action Frame ---
        results_frame = ctk.CTkFrame(tab)
        results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        results_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(results_frame, text="Calculate W-H Plot", command=self._on_wh_calculate).grid(row=0, column=0,
                                                                                                    padx=10, pady=10)

        self.wh_size_label = ctk.CTkLabel(results_frame, text="Size (Å): -")
        self.wh_size_label.grid(row=0, column=1, sticky="w")
        self.wh_strain_label = ctk.CTkLabel(results_frame, text="Strain: -")
        self.wh_strain_label.grid(row=1, column=1, sticky="w")
        self.wh_rsquared_label = ctk.CTkLabel(results_frame, text="R-squared: -")
        self.wh_rsquared_label.grid(row=2, column=1, sticky="w")

    def _on_scherrer_calculate(self):
        selected = self.scherrer_peak_combo.get()
        if not selected: return
        peak_index = int(selected.split(':')[0])
        self.runner.run_scherrer(peak_index)

    def _on_wh_calculate(self):
        self.runner.run_williamson_hall()

    def show_scherrer_result(self, result_text):
        self.scherrer_result_label.configure(text=result_text)

    def display_wh_plot(self, plot_data):
        self.wh_ax.clear()
        self.wh_ax.scatter(plot_data['x_data'], plot_data['y_data'], label='Data Points')
        self.wh_ax.plot(plot_data['fit_line_x'], plot_data['fit_line_y'], 'r-', label='Linear Fit')
        self.wh_ax.set_xlabel("4sin(θ)")
        self.wh_ax.set_ylabel("βcos(θ) [rad]")
        self.wh_ax.set_title("Williamson-Hall Plot")
        self.wh_ax.grid(True)
        self.wh_ax.legend()
        self.wh_figure.tight_layout()
        self.wh_canvas.draw()

    def update_wh_results(self, size, strain, r_squared):
        self.wh_size_label.configure(text=f"Size (Å): {size:.2f}")
        self.wh_strain_label.configure(text=f"Strain: {strain:.5f}")
        self.wh_rsquared_label.configure(text=f"R-squared: {r_squared:.4f}")


# Standalone test
if __name__ == '__main__':
    class MockRunner:
        def run_scherrer(self, peak_index):
            print(f"Runner: Calculating Scherrer for peak index {peak_index}")
            app.plugin_window.show_scherrer_result("Result: 150.25 Å")

        def run_williamson_hall(self):
            print("Runner: Calculating W-H plot")
            # Fake plot data
            plot_data = {
                'x_data': pd.Series([0.1, 0.2, 0.3, 0.4]),
                'y_data': pd.Series([0.005, 0.006, 0.007, 0.008]),
                'fit_line_x': pd.Series([0, 0.4]),
                'fit_line_y': pd.Series([0.004, 0.008])
            }
            app.plugin_window.display_wh_plot(plot_data)
            app.plugin_window.update_wh_results(450.1, 0.0015, 0.998)


    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Microstructure UI Test")
            ctk.CTkLabel(self, text="Main App Window").pack(pady=20)
            self.runner = MockRunner()
            self.peaks_df = pd.DataFrame({
                'angle': [20, 30, 40],
                'fwhm_angle': [0.1, 0.2, 0.3]
            })
            ctk.CTkButton(self, text="Launch Plugin", command=self.launch).pack(pady=20)

        def launch(self):
            self.plugin_window = MicrostructureWindow(self, self.runner, self.peaks_df)


    app = App()
    app.mainloop()