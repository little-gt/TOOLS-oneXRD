import customtkinter as ctk
from tkinter import Listbox, Scrollbar, END, SINGLE


class DatabaseFrame(ctk.CTkFrame):
    """
    A frame for displaying and interacting with saved experiments
    in the database.
    """

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()
        self.update_view_state(has_data=False)

    def _create_widgets(self):
        """Creates and places all widgets in the frame."""
        db_label = ctk.CTkLabel(self, text="Project Database", font=ctk.CTkFont(weight="bold"))
        db_label.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=10)

        list_frame = ctk.CTkFrame(self, fg_color="transparent")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.experiment_listbox = Listbox(
            list_frame,
            selectmode=SINGLE,
            bg="#2B2B2B",
            fg="white",
            selectbackground="#1F6AA5",
            borderwidth=0,
            highlightthickness=0
        )
        self.experiment_listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = Scrollbar(list_frame, command=self.experiment_listbox.yview, orient="vertical")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.experiment_listbox.config(yscrollcommand=scrollbar.set)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=10, pady=10)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.save_button = ctk.CTkButton(button_frame, text="Save", command=self.controller.save_project)
        self.save_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.load_button = ctk.CTkButton(button_frame, text="Load", command=self._on_load_clicked)
        self.load_button.grid(row=0, column=1, padx=5, sticky="ew")

        self.delete_button = ctk.CTkButton(button_frame, text="Delete", fg_color="#D2691E", hover_color="#B85B1A",
                                           command=self._on_delete_clicked)
        self.delete_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def update_experiment_list(self, experiments):
        """Clears and repopulates the list of experiments."""
        self.experiment_listbox.delete(0, END)
        self._experiment_map = {}
        for i, (exp_id, name, ts) in enumerate(experiments):
            display_text = f" {name} ({ts.split('.')[0]})"
            self.experiment_listbox.insert(END, display_text)
            self._experiment_map[i] = exp_id

    def _on_load_clicked(self):
        """Handles the load button click."""
        selected_indices = self.experiment_listbox.curselection()
        if not selected_indices:
            self.controller.show_error("Selection Error", "Please select an experiment to load.")
            return
        selected_idx = selected_indices[0]
        exp_id = self._experiment_map.get(selected_idx)
        if exp_id is not None:
            self.controller.load_from_db(exp_id)

    def _on_delete_clicked(self):
        """Handles the delete button click."""
        selected_indices = self.experiment_listbox.curselection()
        if not selected_indices:
            self.controller.show_error("Selection Error", "Please select an experiment to delete.")
            return
        selected_idx = selected_indices[0]
        exp_id = self._experiment_map.get(selected_idx)
        if exp_id is not None:
            self.controller.delete_from_db(exp_id)

    def update_view_state(self, has_data):
        """Enables or disables the 'Save' button."""
        self.save_button.configure(state="normal" if has_data else "disabled")


# =============================================================================
# Standalone Test Block (Corrected)
# =============================================================================

if __name__ == '__main__':
    class MockController:
        def __init__(self, app_ref):
            self.app = app_ref
            self.dummy_experiments = [
                (1, "NaCl_Run1", "2024-01-01 10:00:00.123"),
                (2, "Quartz_Standard", "2024-01-02 11:30:00.456"),
                (3, "Unknown_Sample", "2024-01-03 14:00:00.789")
            ]

        def save_project(self): print("Controller: Save Project called")

        def load_from_db(self, exp_id): print(f"Controller: Load from DB called with ID: {exp_id}")

        def delete_from_db(self, exp_id):
            print(f"Controller: Delete from DB called with ID: {exp_id}")
            self.dummy_experiments = [exp for exp in self.dummy_experiments if exp[0] != exp_id]
            self.app.db_frame.update_experiment_list(self.dummy_experiments)

        def show_error(self, title, message): print(f"ERROR: {title} - {message}")


    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("DatabaseFrame Test")
            self.geometry("350x450")

            # --- FIX: Main container frame ---
            main_container = ctk.CTkFrame(self)
            main_container.pack(fill="both", expand=True, padx=10, pady=10)

            self.controller = MockController(self)

            # The DatabaseFrame lives inside the main container
            self.db_frame = DatabaseFrame(main_container, self.controller)
            self.db_frame.pack(side="top", fill="both", expand=True)

            # Populate the list for the test
            self.db_frame.update_experiment_list(self.controller.dummy_experiments)

            # --- FIX: The test button now correctly calls its own method ---
            self.frame_has_data = False
            self.toggle_button = ctk.CTkButton(main_container, text="Toggle 'has_data' Flag", command=self.toggle_frame)
            self.toggle_button.pack(side="bottom", pady=10, fill="x")

        def toggle_frame(self):
            """Simulates loading or clearing data in the project."""
            self.frame_has_data = not self.frame_has_data
            self.db_frame.update_view_state(has_data=self.frame_has_data)
            print(
                f"Controller simulated 'has_data' = {self.frame_has_data}. Save button should be {'enabled' if self.frame_has_data else 'disabled'}.")


    app = App()
    app.mainloop()
