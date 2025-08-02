# oneXRD Plugin API Documentation

## 1. Introduction

Welcome to the **oneXRD** Plugin API!

This system is designed to make extending the functionality of **oneXRD** as simple and safe as possible. A plugin is a self-contained Python package that, when placed in the correct directory, can add new UI elements and perform custom analysis using the main application's data.

The core of this system is the `PluginAPI` object, which is passed to your plugin upon registration. This object acts as a safe and stable "bridge" to the main application.

## 2. Recommended Plugin Architecture

To ensure stability and maintainability, we strongly recommend a three-part architecture for any plugin that requires its own user interface.

1.  **`__init__.py` (The Entry Point):** This file is responsible for registering the plugin with the main application and creating the link between your plugin's UI and its logic.
2.  **`ui.py` (The View):** This file should define a class that inherits from `customtkinter.CTkToplevel`. It contains all the UI widgets for your plugin's window and is responsible only for displaying information and capturing user input. It should not contain any complex analysis logic.
3.  **`runner.py` or `logic.py` (The Controller):** This file should contain a class that holds the actual analysis logic. The UI class will call methods on this "runner" class to perform tasks. This keeps your complex code separate from your UI code, preventing the interface from freezing during long operations.

## 3. The `PluginAPI` Class Reference

The `api` object passed to your `register_plugin` function is an instance of the `PluginAPI` class. It provides the following methods:

---

### `get_main_window()`
Returns a reference to the main application window instance. **This is essential for parenting your plugin's `CTkToplevel` window.**

*   **Returns:** `ctk.CTk` object (the main window).

---

### `get_project()`
Returns a **deep copy** of the entire current `Project` object. This is your primary way to get data safely.

*   **Returns:** A `Project` object.

---

### `get_experimental_data()`
A convenience method that directly returns a deep copy of the currently loaded experimental `XRDData` object.

*   **Returns:** An `XRDData` object, or `None` if no experimental data is loaded.

---

### `add_menu_item(menu_name, action_name, callback_function)`
Adds a clickable action to the main window's menubar.

*   **Args:**
    *   `menu_name` (str): The name of the top-level menu (e.g., "Tools", "Analysis").
    *   `action_name` (str): The text for the menu item (e.g., "Batch Processing...").
    *   `callback_function` (callable): The function to execute on click. **Crucially, use a `lambda` to pass the `api` object to your launch function.** (See example below).

---

### `log(message, level='info')`
Writes a message to the main application's central log console.

*   **Args:**
    *   `message` (str): The message to log.
    *   `level` (str): `'info'`, `'warning'`, or `'error'`.

## 4. Full Example: Peak Area Calculator

This example follows the recommended architecture to create a tool that calculates the area of a user-selected peak.

### Step 1: File Structure

```
plugins/
└── peak_calculator/
    ├── __init__.py      <-- Entry Point & Registration
    ├── ui.py            <-- The Plugin's Pop-up Window
    └── logic.py         <-- The Analysis Logic
```

### Step 2: The Logic (`logic.py`)

First, we define the class that does the actual work.

```python
# plugins/peak_calculator/logic.py
import numpy as np
from scipy.integrate import simps # Using Simpson's rule for integration

class CalculatorLogic:
    def __init__(self, api, ui):
        self.api = api
        self.ui = ui

    def calculate_area(self, peak_index, window_fwhm):
        """Calculates the area of a selected peak."""
        exp_data = self.api.get_experimental_data()
        if exp_data is None or exp_data.peaks_df.empty:
            self.api.log("No peak data to analyze.", level='warning')
            return

        try:
            peak_info = exp_data.peaks_df.iloc[peak_index]
            
            # Isolate data window around the peak
            center = peak_info['angle']
            fwhm = peak_info['fwhm_angle']
            half_width = fwhm * window_fwhm / 2.0
            mask = (exp_data.processed_angles >= center - half_width) & (exp_data.processed_angles <= center + half_width)
            
            angles_window = exp_data.processed_angles[mask]
            intensities_window = exp_data.processed_intensities[mask]

            # Calculate area using Simpson's rule
            area = simps(intensities_window, angles_window)
            
            self.ui.show_result(f"Area for peak at {center:.2f}°: {area:.2f}")

        except Exception as e:
            self.api.log(f"Calculation failed: {e}", level='error')
            self.ui.show_result(f"Error: {e}")
```

### Step 3: The User Interface (`ui.py`)

Now, we create the pop-up window. It knows nothing about Simpson's rule; it only knows how to call the logic runner.

```python
# plugins/peak_calculator/ui.py
import customtkinter as ctk

class CalculatorWindow(ctk.CTkToplevel):
    def __init__(self, master, runner, peaks_df):
        super().__init__(master)
        self.runner = runner
        self.title("Peak Area Calculator")
        self.grab_set() # Make window modal

        ctk.CTkLabel(self, text="Select a Peak:").pack(padx=10, pady=5)
        
        peak_options = [f"{i}: {row['angle']:.2f}°" for i, row in peaks_df.iterrows()]
        self.peak_combo = ctk.CTkComboBox(self, values=peak_options)
        self.peak_combo.pack(padx=10, pady=5)

        ctk.CTkLabel(self, text="Integration Width (multiple of FWHM):").pack(padx=10, pady=5)
        self.width_entry = ctk.CTkEntry(self)
        self.width_entry.insert(0, "3.0")
        self.width_entry.pack(padx=10, pady=5)

        ctk.CTkButton(self, text="Calculate", command=self.on_calculate).pack(padx=10, pady=10)
        
        self.result_label = ctk.CTkLabel(self, text="Result: -")
        self.result_label.pack(padx=10, pady=10)

    def on_calculate(self):
        try:
            peak_index = self.peak_combo.get().split(':')[0]
            width_multiplier = float(self.width_entry.get())
            self.runner.calculate_area(int(peak_index), width_multiplier)
        except Exception as e:
            self.show_result(f"Invalid input: {e}")

    def show_result(self, message):
        self.result_label.configure(text=message)
```

### Step 4: The Entry Point (`__init__.py`)

Finally, we create the entry point to tie it all together.

```python
# plugins/peak_calculator/__init__.py
from .ui import CalculatorWindow
from .logic import CalculatorLogic

def launch_calculator(api):
    """The main launch function for our plugin."""
    exp_data = api.get_experimental_data()
    if exp_data is None or exp_data.peaks_df.empty:
        api.log("Cannot launch Peak Calculator: No peaks found.", level='warning')
        return

    main_window = api.get_main_window()
    
    # Create the logic handler first
    # Pass it the API so it can get data
    logic = CalculatorLogic(api, None)

    # Create the UI window
    # Pass it the main window (as parent) and the logic handler
    ui = CalculatorWindow(main_window, logic, exp_data.peaks_df)
    
    # Give the logic handler a reference to the UI so it can send results back
    logic.ui = ui

def register_plugin(api):
    """The required entry point for the plugin."""
    api.add_menu_item(
        menu_name="Analysis",
        action_name="Peak Area Calculator...",
        # Use a lambda to pass the api object to our launcher
        callback_function=lambda: launch_calculator(api)
    )
```