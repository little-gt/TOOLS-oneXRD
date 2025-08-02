import customtkinter as ctk
import pandas as pd
from tkinter import ttk


class PeakListFrame(ctk.CTkFrame):
    """
    A frame for displaying the list of found peaks in a table.
    """

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()
        self.update_peak_list(pd.DataFrame())  # Initialize with empty DataFrame

    def _create_widgets(self):
        """Creates and places all widgets in the frame."""
        label = ctk.CTkLabel(self, text="Identified Peaks", font=ctk.CTkFont(weight="bold"))
        label.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=10)

        # --- Treeview for the peak list ---
        style = ttk.Style(self)
        # Use the customtkinter theme colors
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2B2B2B",
                        foreground="white",
                        fieldbackground="#2B2B2B",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background="#565B5E",
                        foreground="white",
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[('active', '#6A7073')])

        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=('angle', 'intensity', 'prominence', 'fwhm'), show='headings')
        self.tree.heading('#0', text='')
        self.tree.heading('angle', text='Angle (2θ)')
        self.tree.heading('intensity', text='Intensity')
        self.tree.heading('prominence', text='Prominence')
        self.tree.heading('fwhm', text='FWHM')

        self.tree.column('angle', width=100, anchor='center')
        self.tree.column('intensity', width=100, anchor='center')
        self.tree.column('prominence', width=100, anchor='center')
        self.tree.column('fwhm', width=100, anchor='center')

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

    def update_peak_list(self, peaks_df):
        """
        Clears and repopulates the peak list table.

        Args:
            peaks_df (pd.DataFrame): DataFrame containing the peak information.
        """
        # Clear existing items
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insert new items from the DataFrame
        if peaks_df is not None and not peaks_df.empty:
            for index, row in peaks_df.iterrows():
                # Format the values for display
                angle_val = f"{row.get('angle', 0):.4f}"
                intensity_val = f"{row.get('intensity', 0):.2f}"
                prominence_val = f"{row.get('prominence', 0):.2f}"
                fwhm_val = f"{row.get('fwhm_angle', 0):.4f}"

                self.tree.insert('', 'end', values=(angle_val, intensity_val, prominence_val, fwhm_val))


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    class MockController:
        pass


    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("PeakListFrame Test")
            self.geometry("500x350")

            container = ctk.CTkFrame(self)
            container.pack(fill="both", expand=True, padx=10, pady=10)

            self.controller = MockController()
            self.peak_list_frame = PeakListFrame(container, self.controller)
            self.peak_list_frame.pack(fill="both", expand=True)

            # Button to simulate finding peaks and updating the list
            self.test_button = ctk.CTkButton(container, text="Populate with Test Data", command=self.run_test)
            self.test_button.pack(pady=10)

        def run_test(self):
            print("Simulating peak finding and updating list...")
            # Create a sample DataFrame like the one from the analysis module
            test_data = {
                'angle': [29.98, 33.12, 45.05],
                'intensity': [1005.6, 309.2, 89.4],
                'prominence': [1015.1, 298.6, 104.1],
                'fwhm_angle': [0.714, 1.788, 0.506]
            }
            test_df = pd.DataFrame(test_data)
            self.peak_list_frame.update_peak_list(test_df)
            print("Update complete.")


    app = App()
    app.mainloop()
