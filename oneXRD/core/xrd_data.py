import numpy as np
import pandas as pd
import os


class XRDData:
    """
    A container class to hold all data associated with a single XRD pattern.

    This class acts as a centralized data object that can be passed between
    different parts of the application (e.g., UI components, analysis modules).
    """

    def __init__(self, raw_angles, raw_intensities, filename=None, is_reference=False):
        """
        Initializes the XRDData object.

        Args:
            raw_angles (np.ndarray): The original, unmodified 2-theta angles.
            raw_intensities (np.ndarray): The original, unmodified intensities.
            filename (str, optional): The original filename of the data. Defaults to None.
            is_reference (bool, optional): True if this is a theoretical reference
                                           pattern (e.g., from a CIF file). Defaults to False.
        """
        # --- Core Data ---
        self.filename = filename
        self.is_reference = is_reference

        self.raw_angles = np.copy(raw_angles)
        self.raw_intensities = np.copy(raw_intensities)

        # --- Processed Data (will be modified by analysis steps) ---
        self.processed_angles = np.copy(raw_angles)
        self.processed_intensities = np.copy(raw_intensities)

        # --- Analysis Results ---
        self.background_curve = None
        self.peaks_df = pd.DataFrame()  # Always an empty DataFrame initially

    @property
    def display_name(self):
        """A clean name for display in the UI."""
        if self.is_reference:
            base = os.path.basename(self.filename) if self.filename else "Reference"
            return f"{base} (Ref)"
        return os.path.basename(self.filename) if self.filename else "Untitled"

    def set_background(self, background_curve):
        """
        Stores the background curve and calculates the subtracted intensities.

        Args:
            background_curve (np.ndarray): The calculated background to apply.
        """
        self.background_curve = background_curve
        self.processed_intensities = self.raw_intensities - self.background_curve
        print("INFO: Background curve set and processed intensities updated.")

    def set_peaks(self, peaks_dataframe):
        """
        Stores the DataFrame of found peaks.

        Args:
            peaks_dataframe (pd.DataFrame): The DataFrame from the peak_finding module.
        """
        self.peaks_df = peaks_dataframe
        print(f"INFO: Stored {len(peaks_dataframe)} peaks.")

    def reset_processing(self):
        """Resets all analysis results and reverts to the raw data state."""
        self.processed_intensities = np.copy(self.raw_intensities)
        self.background_curve = None
        self.peaks_df = pd.DataFrame()
        print("INFO: All processing steps have been reset.")

    def __repr__(self):
        """String representation for debugging."""
        status = "Processed" if self.background_curve is not None else "Raw"
        num_peaks = len(self.peaks_df)
        return f"<XRDData '{self.display_name}' | Status: {status} | Peaks: {num_peaks}>"


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    print("--- Testing XRDData class ---")

    # --- 1. Initialization ---
    print("\n[Test 1] Initializing object...")
    raw_angles = np.linspace(10, 20, 100)
    raw_intensities = np.random.rand(100) * 100 + 10
    xrd_obj = XRDData(raw_angles, raw_intensities, filename="C:/data/test.xy")

    assert xrd_obj.display_name == "test.xy"
    assert np.array_equal(xrd_obj.raw_intensities, xrd_obj.processed_intensities)
    assert xrd_obj.background_curve is None
    assert xrd_obj.peaks_df.empty
    print(f"  Initial state: {xrd_obj}")
    print("  --> SUCCESS")

    # --- 2. Set Background ---
    print("\n[Test 2] Setting background...")
    dummy_background = np.ones(100) * 10
    xrd_obj.set_background(dummy_background)

    assert np.array_equal(xrd_obj.background_curve, dummy_background)
    assert np.array_equal(xrd_obj.processed_intensities, xrd_obj.raw_intensities - 10)
    print(f"  State after background: {xrd_obj}")
    print("  --> SUCCESS")

    # --- 3. Set Peaks ---
    print("\n[Test 3] Setting peaks...")
    dummy_peaks = pd.DataFrame({'angle': [12.5, 15.8], 'intensity': [95, 88]})
    xrd_obj.set_peaks(dummy_peaks)

    assert not xrd_obj.peaks_df.empty
    assert len(xrd_obj.peaks_df) == 2
    print(f"  State after finding peaks: {xrd_obj}")
    print("  --> SUCCESS")

    # --- 4. Reset Processing ---
    print("\n[Test 4] Resetting all processing...")
    xrd_obj.reset_processing()

    assert np.array_equal(xrd_obj.raw_intensities, xrd_obj.processed_intensities)
    assert xrd_obj.background_curve is None
    assert xrd_obj.peaks_df.empty
    print(f"  State after reset: {xrd_obj}")
    print("  --> SUCCESS")

    # --- 5. Reference Pattern ---
    print("\n[Test 5] Initializing a reference pattern...")
    ref_obj = XRDData(raw_angles, raw_intensities, filename="NaCl.cif", is_reference=True)
    assert ref_obj.display_name == "NaCl.cif (Ref)"
    print(f"  Reference object: {ref_obj}")
    print("  --> SUCCESS")

