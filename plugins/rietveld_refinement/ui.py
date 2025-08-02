import customtkinter as ctk
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class RietveldWindow(ctk.CTkToplevel):
    """The user interface for the Rietveld Refinement plugin."""

    def __init__(self, master, runner):
        super().__init__(master)
        self.runner = runner  # The RietveldEngine instance
        self.runner.ui = self  # Give the engine a reference back to this UI

        self.title("Rietveld Refinement")
        self.geometry("950x800")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # The plot area expands
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        # --- 1. Input Frame ---
        self._create_input_frame()

        # --- 2. Settings Frame ---
        self._create_settings_frame()

        # --- 3. Results Frame (Plot and Info) ---
        self._create_results_frame()

    def _create_input_frame(self):
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(input_frame, text="1. Inputs", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3,
                                                                                          sticky="w", padx=10, pady=5)

        ctk.CTkLabel(input_frame, text="Experimental Data:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.exp_path_entry = ctk.CTkEntry(input_frame, state="readonly")
        self.exp_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse...", command=self._browse_exp).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkLabel(input_frame, text="CIF File:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.cif_path_entry = ctk.CTkEntry(input_frame, state="readonly")
        self.cif_path_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse...", command=self._browse_cif).grid(row=2, column=2, padx=10, pady=5)

    def _create_settings_frame(self):
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, padx=10, pady=0, sticky="ew")
        settings_frame.grid_columnconfigure(4, weight=1)
        ctk.CTkLabel(settings_frame, text="2. Settings", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                               columnspan=5, sticky="w",
                                                                                               padx=10, pady=5)

        self.refine_bg_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Background", variable=self.refine_bg_var).grid(row=1, column=0, padx=10,
                                                                                             pady=5)
        self.refine_cell_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Unit Cell", variable=self.refine_cell_var).grid(row=1, column=1, padx=10,
                                                                                              pady=5)
        self.refine_shape_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Peak Shape", variable=self.refine_shape_var).grid(row=1, column=2,
                                                                                                padx=10, pady=5)

        ctk.CTkLabel(settings_frame, text="Cycles:").grid(row=1, column=3, padx=(20, 5), pady=5)
        self.cycles_entry = ctk.CTkEntry(settings_frame, width=50)
        self.cycles_entry.insert(0, "6")
        self.cycles_entry.grid(row=1, column=4, padx=(0, 10), pady=5, sticky="w")

        self.run_button = ctk.CTkButton(settings_frame, text="Run Refinement", command=self._on_run_clicked)
        self.run_button.grid(row=2, column=0, columnspan=5, padx=10, pady=10, sticky="ew")

    def _create_results_frame(self):
        results_frame = ctk.CTkFrame(self)
        results_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=3)  # Plot gets more space
        results_frame.grid_columnconfigure(1, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        ctk.CTkLabel(results_frame, text="3. Results", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                             columnspan=2, sticky="nw",
                                                                                             padx=10, pady=5)

        # Plot
        self.figure = Figure(dpi=100)
        self.ax1, self.ax2 = self.figure.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        self.canvas = FigureCanvasTkAgg(self.figure, results_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=(30, 5))

        # Info and Log
        info_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(30, 5))
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(2, weight=1)

        self.rwp_var = ctk.StringVar(value="Rwp: --")
        ctk.CTkLabel(info_frame, textvariable=self.rwp_var, font=ctk.CTkFont(size=14, weight="bold")).grid(row=0,
                                                                                                           column=0,
                                                                                                           sticky="w")
        self.chi2_var = ctk.StringVar(value="χ²: --")
        ctk.CTkLabel(info_frame, textvariable=self.chi2_var, font=ctk.CTkFont(size=14, weight="bold")).grid(row=1,
                                                                                                            column=0,
                                                                                                            sticky="w")

        self.log_textbox = ctk.CTkTextbox(info_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=2, column=0, sticky="nsew", pady=10)

    def _browse_exp(self):
        path = filedialog.askopenfilename(title="Select Experimental Data");
        if path: self.exp_path_entry.configure(state="normal"); self.exp_path_entry.delete(0,
                                                                                           "end"); self.exp_path_entry.insert(
            0, path); self.exp_path_entry.configure(state="readonly")

    def _browse_cif(self):
        path = filedialog.askopenfilename(title="Select CIF File");
        if path: self.cif_path_entry.configure(state="normal"); self.cif_path_entry.delete(0,
                                                                                           "end"); self.cif_path_entry.insert(
            0, path); self.cif_path_entry.configure(state="readonly")

    def _on_run_clicked(self):
        exp_path = self.exp_path_entry.get()
        cif_path = self.cif_path_entry.get()
        if not exp_path or not cif_path:
            self.log_message("Please provide both experimental and CIF file paths.", "error")
            return

        settings = {
            'refine_background': self.refine_bg_var.get(),
            'refine_cell': self.refine_cell_var.get(),
            'refine_peak_shape': self.refine_shape_var.get()
        }
        cycles = int(self.cycles_entry.get() or 5)

        self.run_button.configure(state="disabled", text="Running...")
        self.log_message("Starting refinement...", "info")
        # The runner will perform the work in a separate thread in a real app
        self.runner.start_refinement(exp_path, cif_path, settings, cycles)

    def log_message(self, message, level="info"):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{level.upper()}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def update_results(self, results):
        self.rwp_var.set(f"Rwp: {results['rwp']:.4f}%")
        self.chi2_var.set(f"χ²: {results['chi2']:.4f}")
        self.update_plot(results)
        self.run_button.configure(state="normal", text="Run Refinement")

    def update_plot(self, results):
        self.ax1.clear();
        self.ax2.clear()
        self.ax1.plot(results['x'], results['y_obs'], 'b.', markersize=2, label='Observed')
        self.ax1.plot(results['x'], results['y_calc'], 'r-', label='Calculated')
        self.ax1.plot(results['x'], results['y_bkg'], 'g--', label='Background')
        self.ax1.set_ylabel("Intensity");
        self.ax1.legend()

        self.ax2.plot(results['x'], results['y_diff'], 'k-')
        self.ax2.axhline(0, color='r', linestyle='--')
        self.ax2.set_xlabel("Angle (2θ)");
        self.ax2.set_ylabel("Difference")
        self.figure.tight_layout()
        self.canvas.draw()


# Standalone Test Block
if __name__ == '__main__':
    import numpy as np


    class MockEngine:
        def __init__(self, ui): self.ui = ui

        def start_refinement(self, exp, cif, settings, cycles):
            self.ui.log_message("MockEngine: Refinement started.", "info")
            # Simulate work
            self.ui.after(2000, self.finish_refinement)

        def finish_refinement(self):
            # Create fake but plausible results data
            x = np.linspace(10, 80, 1000)
            y_obs = 100 + 500 * np.exp(-(x - 30) ** 2 / 0.5) + np.random.rand(1000) * 10
            y_calc = 100 + 500 * np.exp(-(x - 30) ** 2 / 0.5)
            results = {
                'rwp': 8.5432, 'chi2': 1.8765, 'x': x,
                'y_obs': y_obs, 'y_calc': y_calc, 'y_bkg': np.full_like(x, 100),
                'y_diff': y_obs - y_calc
            }
            self.ui.log_message("MockEngine: Refinement finished.", "success")
            self.ui.update_results(results)


    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Rietveld UI Test")
            mock_engine = MockEngine(None)
            self.rietveld_window = RietveldWindow(self, mock_engine)
            mock_engine.ui = self.rietveld_window


    app = App()
    app.mainloop()