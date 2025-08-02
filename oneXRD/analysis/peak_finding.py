import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths


# =============================================================================
# Custom Exception
# =============================================================================

class PeakFindingError(Exception):
    """Custom exception for errors during peak finding."""
    pass


# =============================================================================
# Peak Finding Function (Corrected)
# =============================================================================

def find_all_peaks(angles, intensities, min_height=None, min_prominence=None, min_width=None):
    """
    Finds peaks in the given XRD data.

    This function is a wrapper around scipy.signal.find_peaks, tailored for XRD
    data and returning a structured pandas DataFrame.

    Args:
        angles (np.ndarray): The array of 2-theta angles.
        intensities (np.ndarray): The array of corresponding intensities.
                                 (Should be background-subtracted).
        min_height (float, optional): The minimum height of a peak.
        min_prominence (float, optional): The minimum prominence of a peak.
        min_width (float, optional): The minimum width of a peak in data points.

    Returns:
        pd.DataFrame: A DataFrame containing information about each found peak.
                      Columns include 'angle', 'intensity', 'prominence',
                      and 'fwhm_angle'. Returns an empty DataFrame if no
                      peaks are found.
    """
    try:
        peak_indices, properties = find_peaks(
            intensities,
            height=min_height,
            prominence=min_prominence,
            width=min_width
        )

        if len(peak_indices) == 0:
            return pd.DataFrame(columns=['angle', 'intensity', 'prominence', 'fwhm_angle'])

        # --- FIX 1: Safely calculate widths only if peaks were found ---
        widths, _, _, _ = peak_widths(intensities, peak_indices, rel_height=0.5)
        avg_angle_step = np.mean(np.diff(angles))
        fwhm_angles = widths * avg_angle_step

        # --- FIX 2: Use .get() for safe access to optional properties ---
        peak_df = pd.DataFrame({
            'angle': angles[peak_indices],
            'intensity': intensities[peak_indices],
            # If 'prominences' wasn't calculated, fill with NaN
            'prominence': properties.get('prominences', np.nan),
            'fwhm_angle': fwhm_angles
        })

        peak_df = peak_df.sort_values(by='angle').reset_index(drop=True)

        return peak_df

    except Exception as e:
        raise PeakFindingError(f"An unexpected error occurred during peak finding: {e}")


# =============================================================================
# Standalone Test Block (Corrected)
# =============================================================================

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    print("--- Testing peak_finding.py (Corrected) ---")

    # --- 1. Generate realistic fake XRD data ---
    angles = np.linspace(20, 60, 2000)
    peak1 = 1000 * np.exp(-((angles - 30) ** 2) / (2 * 0.3 ** 2))
    peak2 = 300 * np.exp(-((angles - 33) ** 2) / (2 * 0.8 ** 2))
    peak3 = 80 * np.exp(-((angles - 45) ** 2) / (2 * 0.2 ** 2))
    intensities = peak1 + peak2 + peak3 + np.random.normal(0, 5, len(angles))

    # --- 2. Test with basic filtering ---
    print("\n[Test 1] Basic filtering (min_height=50)")
    try:
        peaks_df_1 = find_all_peaks(angles, intensities, min_height=50)
        print("Found peaks:")
        print(peaks_df_1)
        # --- FIX 3: More robust assertion ---
        assert len(peaks_df_1) == 3  # With this low filter, we expect to find all 3 peaks

        plt.figure(figsize=(12, 7))
        plt.plot(angles, intensities, label='Raw Data')
        plt.plot(peaks_df_1['angle'], peaks_df_1['intensity'], 'rx', markersize=10, label='Found Peaks (Test 1)')
        plt.title("Peak Finding Test 1 (min_height=50)")
        plt.xlabel("Angle (2-Theta)")
        plt.ylabel("Intensity")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.show()
        print("  --> SUCCESS")

    except (PeakFindingError, AssertionError) as e:
        print(f"  --> FAILED: {e}")

    # --- 3. Test with more stringent prominence filtering ---
    print("\n[Test 2] Stringent filtering (min_prominence=100)")
    try:
        peaks_df_2 = find_all_peaks(angles, intensities, min_prominence=100)
        print("Found peaks:")
        print(peaks_df_2)
        # --- FIX 4: More logical assertion ---
        # This proves the filter is working by reducing the number of found peaks.
        assert len(peaks_df_2) < len(peaks_df_1)

        plt.figure(figsize=(12, 7))
        plt.plot(angles, intensities, label='Raw Data')
        plt.plot(peaks_df_2['angle'], peaks_df_2['intensity'], 'go', markerfacecolor='none', markersize=12,
                 label='Found Peaks (Test 2)')
        plt.title("Peak Finding Test 2 (min_prominence=100)")
        plt.xlabel("Angle (2-Theta)")
        plt.ylabel("Intensity")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.show()
        print("  --> SUCCESS")

    except (PeakFindingError, AssertionError) as e:
        print(f"  --> FAILED: {e}")
