import customtkinter as ctk
from tkinter import ttk, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt  # Import for color mapping


class QpaWindow(ctk.CTkToplevel):
    """The redesigned UI window for QPA with integrated visualizations."""

    def __init__(self, master, runner, experimental_data):
        super().__init__(master)
        self.runner = runner
        self.experimental_data = experimental_data
        self.reference_patterns = list(runner.api.get_project().reference_data.values())

        self.title("Quantitative Phase Analysis (RIR)")
        self.geometry("1100x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grab_set()

        self._create_widgets()
        self._populate_from_project()

    def _create_widgets(self):
        # --- Main Tab View ---
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        self.tab_setup = self.tab_view.add("Setup & Edit")
        self.tab_results = self.tab_view.add("Results & Visualization")
        self.tab_view.set("Setup & Edit")  # Start on the first tab

        # --- FIX: The line that caused the error has been REMOVED. ---
        # self.tab_view.tab("Results & Visualization").configure(state="disabled") # This was the error

        # --- Populate Tab 1: Setup & Edit ---
        self._create_setup_tab(self.tab_setup)

        # --- Populate Tab 2: Results & Visualization ---
        self._create_results_tab(self.tab_results)

    def _create_setup_tab(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        # The two-panel inspector layout
        list_frame = ctk.CTkFrame(tab);
        list_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_frame, text="1. Add & Select Phases", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                                      pady=5, padx=10,
                                                                                                      sticky="w")
        self.tree = self._create_treeview(list_frame);
        self.tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        list_button_frame = ctk.CTkFrame(list_frame, fg_color="transparent");
        list_button_frame.grid(row=2, column=0, pady=10, sticky="ew")
        ctk.CTkButton(list_button_frame, text="Add Phase...", command=self._on_add_phase).pack(side="left", padx=10)
        ctk.CTkButton(list_button_frame, text="Remove Selected", command=self._on_remove_phase).pack(side="left",
                                                                                                     padx=5)
        self.inspector_frame = ctk.CTkFrame(tab);
        self.inspector_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.inspector_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.inspector_frame, text="2. Edit Selected Phase", font=ctk.CTkFont(weight="bold")).grid(row=0,
                                                                                                                column=0,
                                                                                                                columnspan=2,
                                                                                                                pady=5,
                                                                                                                padx=10,
                                                                                                                sticky="w")
        ctk.CTkLabel(self.inspector_frame, text="Assigned Peak:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        peak_options = [f"{idx}: {row['angle']:.3f}°" for idx, row in self.experimental_data.peaks_df.iterrows()]
        self.peak_combo = ctk.CTkComboBox(self.inspector_frame, values=["N/A"] + peak_options, width=250);
        self.peak_combo.grid(row=1, column=1, padx=10, sticky="ew")
        ctk.CTkLabel(self.inspector_frame, text="RIR Value:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.rir_entry = ctk.CTkEntry(self.inspector_frame);
        self.rir_entry.grid(row=2, column=1, padx=10, sticky="ew")
        self.update_button = ctk.CTkButton(self.inspector_frame, text="Update Phase", command=self._on_update_clicked);
        self.update_button.grid(row=3, column=1, padx=10, pady=20, sticky="e")
        self._set_inspector_state("disabled")
        action_frame = ctk.CTkFrame(tab, fg_color="transparent");
        action_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="e")
        self.calculate_button = ctk.CTkButton(action_frame, text="3. Calculate & View Results",
                                              font=ctk.CTkFont(weight="bold"), command=self._on_calculate);
        self.calculate_button.pack(padx=10)

    def _create_results_tab(self, tab):
        tab.grid_columnconfigure((0, 1), weight=1)
        tab.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Calculation Results", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                            columnspan=2, padx=10,
                                                                                            pady=10, sticky="w")

        self.pie_fig = Figure(figsize=(5, 4), dpi=100, facecolor='#2B2B2B')
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, tab)
        self.pie_canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.peak_fig = Figure(figsize=(5, 4), dpi=100, facecolor='#2B2B2B')
        self.peak_ax = self.peak_fig.add_subplot(111)
        self.peak_canvas = FigureCanvasTkAgg(self.peak_fig, tab)
        self.peak_canvas.get_tk_widget().grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

    def update_results(self, phase_data):
        # --- FIX: Programmatically switch to the results tab ---
        self.tab_view.set("Results & Visualization")

        names = [p['name'] for p in phase_data]
        percents = [p['wt_percent'] for p in phase_data]

        self._update_pie_chart(names, percents)
        self._update_peak_plot(phase_data)

    def _update_pie_chart(self, names, percents):
        self.pie_ax.clear()
        self.pie_ax.pie(percents, labels=names, autopct='%1.1f%%', startangle=90,
                        textprops={'color': "w"},
                        wedgeprops=dict(width=0.4, edgecolor='w'))
        self.pie_ax.set_title("Phase Composition (Wt. %)", color='white')
        self.pie_fig.tight_layout()
        self.pie_canvas.draw()

    def _update_peak_plot(self, phase_data):
        self.peak_ax.clear()
        self.peak_ax.plot(self.experimental_data.processed_angles, self.experimental_data.processed_intensities,
                          label='Experimental Data', color='gray')

        colors = plt.cm.get_cmap('tab10', len(phase_data))
        for i, phase in enumerate(phase_data):
            self.peak_ax.axvline(phase['angle'], color=colors(i), linestyle='--', label=f"{phase['name']} peak")

        self.peak_ax.set_title("Assigned Experimental Peaks", color='white')
        self.peak_ax.set_xlabel("Angle (2θ)", color='white');
        self.peak_ax.set_ylabel("Intensity", color='white')
        self.peak_ax.tick_params(axis='x', colors='white');
        self.peak_ax.tick_params(axis='y', colors='white')
        self.peak_ax.legend();
        self.peak_ax.grid(True, alpha=0.5)
        self.peak_ax.set_facecolor('#3B3B3B')
        self.peak_fig.tight_layout()
        self.peak_canvas.draw()

    # --- All other helper methods (_populate_from_project, _create_treeview, _on_add_phase, etc.)
    # --- are identical to the previous 'optimized' version and do not need to be changed.
    def _populate_from_project(self):
        for ref_data in self.reference_patterns:
            phase_name = ref_data.display_name.replace(" (Ref)", "")
            self.tree.insert('', 'end', values=(phase_name, 'N/A', 'N/A', '1.00', 'N/A'))
        if self.reference_patterns: self.runner.api.log(
            f"Pre-loaded {len(self.reference_patterns)} phases from main project.", "info")

    def _create_treeview(self, parent):
        style = ttk.Style(self);
        style.theme_use("default")
        style.configure("Treeview", background="#2B2B2B", foreground="white", fieldbackground="#2B2B2B", rowheight=25)
        style.configure("Treeview.Heading", background="#565B5E", foreground="white", font=('Arial', 10, 'bold'))
        columns = ('phase', 'peak_angle', 'intensity', 'rir', 'wt_percent')
        tree = ttk.Treeview(parent, columns=columns, show='headings')
        tree.heading('phase', text='Phase');
        tree.heading('peak_angle', text='Peak (2θ)');
        tree.heading('intensity', text='Intensity');
        tree.heading('rir', text='RIR');
        tree.heading('wt_percent', text='Wt. %')
        tree.column('phase', width=200);
        tree.column('peak_angle', width=80);
        tree.column('intensity', width=80);
        tree.column('rir', width=60);
        tree.column('wt_percent', width=80)
        return tree

    def _set_inspector_state(self, state):
        self.peak_combo.configure(state=state);
        self.rir_entry.configure(state=state);
        self.update_button.configure(state=state)
        if state == "disabled": self.peak_combo.set("N/A"); self.rir_entry.delete(0, "end")

    def _on_selection_changed(self, event):
        selected_item = self.tree.focus();
        if not selected_item: self._set_inspector_state("disabled"); return
        self._set_inspector_state("normal");
        values = self.tree.item(selected_item)['values']
        peak_angle = values[1];
        combo_val = "N/A"
        for option in self.peak_combo.cget("values"):
            if str(peak_angle) in option: combo_val = option; break
        self.peak_combo.set(combo_val);
        self.rir_entry.delete(0, "end");
        self.rir_entry.insert(0, values[3])

    def _on_update_clicked(self):
        selected_item = self.tree.focus();
        if not selected_item: return
        try:
            selection = self.peak_combo.get()
            if selection == "N/A":
                peak_angle, intensity = "N/A", "N/A"
            else:
                peak_index = int(selection.split(':')[0]);
                selected_peak = self.experimental_data.peaks_df.iloc[peak_index]
                peak_angle = f"{selected_peak['angle']:.3f}";
                intensity = f"{selected_peak['intensity']:.1f}"
            rir = f"{float(self.rir_entry.get()):.2f}"
            self.tree.set(selected_item, 'peak_angle', peak_angle);
            self.tree.set(selected_item, 'intensity', intensity);
            self.tree.set(selected_item, 'rir', rir)
        except (ValueError, TypeError) as e:
            self.runner.api.log(f"Invalid input for RIR value: {e}", level="error")

    def _on_add_phase(self):
        filepath = filedialog.askopenfilename(title="Select CIF File", filetypes=[("CIF Files", "*.cif")]);
        if not filepath: return
        import os;
        phase_name = os.path.basename(filepath)
        self.tree.insert('', 'end', values=(phase_name, 'N/A', 'N/A', '1.00', 'N/A'))

    def _on_remove_phase(self):
        selected_item = self.tree.focus();
        if selected_item: self.tree.delete(selected_item)

    def _on_calculate(self):
        phase_data = [];
        items = self.tree.get_children()
        for item in items:
            values = self.tree.item(item)['values']
            try:
                phase_data.append({'name': values[0], 'angle': float(values[1]), 'intensity': float(values[2]),
                                   'rir': float(values[3])})
            except (ValueError, TypeError):
                self.runner.api.log(f"Invalid data for phase '{values[0]}'. Please assign a peak and valid RIR.",
                                    level="error");
                return
        self.runner.run_calculation(phase_data)