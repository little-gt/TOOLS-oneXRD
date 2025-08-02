import customtkinter as ctk
from tkinter import filedialog


class BatchWindow(ctk.CTkToplevel):
    """
    The user interface for the batch processing plugin.
    This window allows users to select a folder, define analysis parameters,
    and run a batch job.
    """

    def __init__(self, master, runner):
        super().__init__(master)
        self.runner = runner  # The logic controller for this plugin

        self.title("Batch Processing")
        self.geometry("600x700")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Log box expands

        self._create_widgets()
        self.grab_set()  # Make this window modal

    def _create_widgets(self):
        """Creates and lays out all the UI widgets."""
        # --- Input Frame ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text="Input Folder:").grid(row=0, column=0, padx=10, pady=10)
        self.folder_entry = ctk.CTkEntry(input_frame, state="readonly")
        self.folder_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(input_frame, text="Browse...", command=self._browse_folder).grid(row=0, column=2, padx=10,
                                                                                       pady=10)

        # --- Parameters Frame ---
        params_frame = ctk.CTkFrame(self)
        params_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        params_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(params_frame, text="Analysis Parameters", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                                     columnspan=4,
                                                                                                     pady=5)

        self.bg_var = ctk.StringVar(value="on")
        ctk.CTkCheckBox(params_frame, text="Subtract Background", variable=self.bg_var).grid(row=1, column=0, padx=10)
        self.bg_iter_entry = ctk.CTkEntry(params_frame, placeholder_text="Iterations (e.g., 50)")
        self.bg_iter_entry.grid(row=1, column=1)

        self.pk_var = ctk.StringVar(value="on")
        ctk.CTkCheckBox(params_frame, text="Find Peaks", variable=self.pk_var).grid(row=2, column=0, padx=10)
        self.pk_prom_entry = ctk.CTkEntry(params_frame, placeholder_text="Min Prominence")
        self.pk_prom_entry.grid(row=2, column=1)

        # --- Output Frame ---
        output_frame = ctk.CTkFrame(self)
        output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        output_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(output_frame, text="Output CSV Name:").grid(row=0, column=0, padx=10, pady=10)
        self.output_name_entry = ctk.CTkEntry(output_frame)
        self.output_name_entry.insert(0, "batch_results.csv")
        self.output_name_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

        # --- Log and Progress Frame ---
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled")
        self.log_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        # --- Action Buttons ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)

        self.run_button = ctk.CTkButton(action_frame, text="Run Batch Process", command=self._run_clicked)
        self.run_button.grid(row=0, column=0, padx=5, sticky="ew")
        self.close_button = ctk.CTkButton(action_frame, text="Close", command=self.destroy)
        self.close_button.grid(row=0, column=1, padx=5, sticky="ew")

    def _browse_folder(self):
        """Opens a dialog to select an input folder."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.configure(state="normal")
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.folder_entry.configure(state="readonly")

    def _get_params(self):
        """Gathers all settings from the UI into a dictionary."""
        params = {
            'input_folder': self.folder_entry.get(),
            'output_name': self.output_name_entry.get(),
            'do_background': self.bg_var.get() == "on",
            'bg_iterations': int(self.bg_iter_entry.get() or 50),
            'do_peaks': self.pk_var.get() == "on",
            'pk_prominence': float(self.pk_prom_entry.get() or 0)
        }
        return params

    def _run_clicked(self):
        """Called when the 'Run' button is clicked. Delegates to the runner."""
        try:
            params = self._get_params()
            if not params['input_folder']:
                self.log_message("ERROR: Please select an input folder.", "error")
                return
            self.run_button.configure(state="disabled")
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            self.log_textbox.configure(state="disabled")
            self.runner.run_batch(params)
        except (ValueError, TypeError) as e:
            self.log_message(f"ERROR: Invalid parameter. Please check your inputs. Details: {e}", "error")

    def log_message(self, message, level="info"):
        """Appends a message to the log box."""
        self.log_textbox.configure(state="normal")
        # In a real app, we might add color-coding for levels
        self.log_textbox.insert("end", f"[{level.upper()}] {message}\n")
        self.log_textbox.see("end")  # Auto-scroll
        self.log_textbox.configure(state="disabled")

    def set_progress(self, value):
        """Sets the progress bar value (0.0 to 1.0)."""
        self.progress_bar.set(value)

    def on_batch_complete(self):
        """Called by the runner when the batch is finished."""
        self.run_button.configure(state="normal")
        self.log_message("Batch process complete!", "success")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    import time


    class MockAPI:
        def log(self, message, level='info'):
            print(f"API_LOG ({level}): {message}")


    class MockRunner:
        """Simulates the plugin's logic controller."""

        def __init__(self, app_ref, ui_ref, api_ref):
            self.app = app_ref
            self.ui = ui_ref
            self.api = api_ref

        def run_batch(self, params):
            self.ui.log_message(f"Starting batch with params: {params}")
            total_files = 10
            for i in range(total_files + 1):
                progress = i / total_files
                self.ui.set_progress(progress)
                if i < total_files:
                    self.ui.log_message(f"Processing file {i + 1} of {total_files}...")
                self.app.update_idletasks()  # Crucial for UI updates
                time.sleep(0.3)  # Simulate work
            self.ui.on_batch_complete()


    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Batch UI Test")
            ctk.CTkLabel(self, text="Main App Window").pack(pady=20)
            self.api = MockAPI()

            self.launch_button = ctk.CTkButton(self, text="Launch Batch Processor", command=self.launch_plugin)
            self.launch_button.pack(pady=20)

        def launch_plugin(self):
            # The runner would be part of the plugin's main logic
            # It gets a reference to the UI window it will control
            runner = MockRunner(self, None, self.api)
            batch_window = BatchWindow(self, runner)
            runner.ui = batch_window  # Give the runner a reference to the UI it controls


    app = App()
    app.mainloop()

