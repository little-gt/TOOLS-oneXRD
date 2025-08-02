import customtkinter as ctk


class AnalysisFrame(ctk.CTkFrame):
    """
    A frame containing all widgets for controlling analysis functions like
    background subtraction and peak finding.
    """

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=0)

        self._create_widgets()
        self.update_view_state(has_data=False)  # Initially disabled

    def _create_widgets(self):
        """Creates and places all widgets in the frame."""
        # --- Background Subtraction Section ---
        bg_label = ctk.CTkLabel(self, text="Background Subtraction", font=ctk.CTkFont(weight="bold"))
        bg_label.grid(row=0, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=10)

        self.bg_method_var = ctk.StringVar(value="Iterative Erosion")
        bg_method_menu = ctk.CTkOptionMenu(self, variable=self.bg_method_var,
                                           values=["Iterative Erosion", "Polynomial"])
        bg_method_menu.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Parameters for background subtraction
        self.bg_poly_order_entry = ctk.CTkEntry(self, placeholder_text="Polynomial Order (e.g., 3)")
        self.bg_poly_order_entry.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="ew")
        self.bg_iterations_entry = ctk.CTkEntry(self, placeholder_text="Iterations (e.g., 50)")
        self.bg_iterations_entry.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")

        apply_bg_button = ctk.CTkButton(self, text="Apply Background", command=self.controller.apply_background)
        apply_bg_button.grid(row=3, column=0, padx=(10, 5), pady=5, sticky="ew")

        clear_bg_button = ctk.CTkButton(self, text="Clear Background", command=self.controller.clear_background)
        clear_bg_button.grid(row=3, column=1, padx=(5, 10), pady=5, sticky="ew")

        # --- Peak Finding Section ---
        peak_label = ctk.CTkLabel(self, text="Peak Finding", font=ctk.CTkFont(weight="bold"))
        peak_label.grid(row=4, column=0, columnspan=2, pady=(20, 5), sticky="w", padx=10)

        self.peak_min_height_entry = ctk.CTkEntry(self, placeholder_text="Min Height")
        self.peak_min_height_entry.grid(row=5, column=0, padx=(10, 5), pady=5, sticky="ew")

        self.peak_min_prominence_entry = ctk.CTkEntry(self, placeholder_text="Min Prominence")
        self.peak_min_prominence_entry.grid(row=5, column=1, padx=(5, 10), pady=5, sticky="ew")

        find_peaks_button = ctk.CTkButton(self, text="Find Peaks", command=self.controller.find_peaks)
        find_peaks_button.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    def get_bg_params(self):
        """Returns a dictionary of background subtraction parameters from the UI."""
        method = self.bg_method_var.get()
        params = {'method': method}
        if method == "Polynomial":
            try:
                params['poly_order'] = int(self.bg_poly_order_entry.get())
            except (ValueError, TypeError):
                # Handle empty or invalid input
                self.controller.show_error("Invalid Input", "Polynomial order must be an integer.")
                return None
        elif method == "Iterative Erosion":
            try:
                params['iterations'] = int(self.bg_iterations_entry.get())
            except (ValueError, TypeError):
                self.controller.show_error("Invalid Input", "Iterations must be an integer.")
                return None
        return params

    def get_peak_params(self):
        """Returns a dictionary of peak finding parameters from the UI."""
        params = {}
        try:
            height_str = self.peak_min_height_entry.get()
            if height_str:
                params['min_height'] = float(height_str)

            prom_str = self.peak_min_prominence_entry.get()
            if prom_str:
                params['min_prominence'] = float(prom_str)
        except (ValueError, TypeError):
            self.controller.show_error("Invalid Input", "Peak finding parameters must be numbers.")
            return None
        return params

    def update_view_state(self, has_data):
        """Enables or disables all widgets based on whether data is loaded."""
        state = "normal" if has_data else "disabled"
        for child in self.winfo_children():
            if isinstance(child, (ctk.CTkButton, ctk.CTkEntry, ctk.CTkOptionMenu)):
                child.configure(state=state)


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    # Create a dummy controller for testing purposes
    class MockController:
        def apply_background(self):
            print("Controller: Apply Background called")
            params = app.analysis_frame.get_bg_params()
            print(f"  Params: {params}")

        def clear_background(self):
            print("Controller: Clear Background called")

        def find_peaks(self):
            print("Controller: Find Peaks called")
            params = app.analysis_frame.get_peak_params()
            print(f"  Params: {params}")

        def show_error(self, title, message):
            print(f"ERROR: {title} - {message}")


    # Create a simple main window to host the frame
    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("AnalysisFrame Test")
            self.geometry("350x400")

            self.controller = MockController()
            self.analysis_frame = AnalysisFrame(self, self.controller)
            self.analysis_frame.pack(side="left", fill="y", expand=False, padx=10, pady=10)

            # Add a button to simulate loading data
            self.toggle_button = ctk.CTkButton(self, text="Enable/Disable Frame", command=self.toggle_frame)
            self.toggle_button.pack(pady=10)
            self.frame_enabled = False

        def toggle_frame(self):
            self.frame_enabled = not self.frame_enabled
            self.analysis_frame.update_view_state(has_data=self.frame_enabled)
            print(f"Frame state enabled: {self.frame_enabled}")


    app = App()
    app.mainloop()
