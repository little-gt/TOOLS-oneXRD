import numpy as np
import pandas as pd
from scipy.stats import linregress


# =============================================================================
# Custom Exception
# =============================================================================

class MicrostructureError(Exception):
    """Custom exception for errors during microstructure analysis."""
    pass


# =============================================================================
# Core Analysis Functions
# =============================================================================

def calculate_scherrer_size(peak_fwhm, peak_angle, wavelength=1.5406, shape_factor_K=0.9):
    """
    Calculates crystallite size using the Scherrer equation for a single peak.

    Args:
        peak_fwhm (float): The full-width at half-maximum (FWHM) of the peak in degrees.
        peak_angle (float): The 2-theta position of the peak in degrees.
        wavelength (float, optional): The X-ray wavelength in Angstroms. Defaults to 1.5406 (Cu K-alpha).
        shape_factor_K (float, optional): The Scherrer shape factor. Defaults to 0.9.

    Returns:
        float: The calculated crystallite size in Angstroms.
    """
    if peak_fwhm <= 0:
        raise MicrostructureError("FWHM must be a positive value.")

    # Convert angles from degrees to radians
    fwhm_rad = np.deg2rad(peak_fwhm)
    theta_rad = np.deg2rad(peak_angle / 2.0)

    # Scherrer equation: D = (K * lambda) / (beta * cos(theta))
    crystallite_size = (shape_factor_K * wavelength) / (fwhm_rad * np.cos(theta_rad))
    return crystallite_size


def calculate_williamson_hall(peaks_df, wavelength=1.5406, shape_factor_K=0.9):
    """
    Performs a Williamson-Hall analysis on a set of peaks.

    Args:
        peaks_df (pd.DataFrame): A DataFrame of found peaks, must contain
                                 'angle' and 'fwhm_angle' columns.
        wavelength (float, optional): The X-ray wavelength in Angstroms. Defaults to 1.5406.
        shape_factor_K (float, optional): The Scherrer shape factor. Defaults to 0.9.

    Returns:
        dict: A dictionary containing all data needed for plotting and results:
              {'x_data', 'y_data', 'fit_line_x', 'fit_line_y',
               'crystallite_size_A', 'strain', 'r_squared'}.
    """
    if len(peaks_df) < 2:
        raise MicrostructureError("Williamson-Hall analysis requires at least 2 peaks.")

    fwhm_rad = np.deg2rad(peaks_df['fwhm_angle'])
    theta_rad = np.deg2rad(peaks_df['angle'] / 2.0)

    # Calculate W-H plot coordinates
    # y = beta * cos(theta)
    # x = 4 * sin(theta)
    y_data = fwhm_rad * np.cos(theta_rad)
    x_data = 4 * np.sin(theta_rad)

    # Perform linear regression: y = m*x + c
    slope, intercept, r_value, _, _ = linregress(x_data, y_data)

    # Extract physical parameters
    # Slope = strain (epsilon)
    strain = slope
    # Y-intercept = (K * lambda) / D
    if intercept <= 0:
        raise MicrostructureError("Fit resulted in a non-positive y-intercept, cannot calculate size.")
    crystallite_size = (shape_factor_K * wavelength) / intercept

    # Prepare data for plotting the fitted line
    fit_line_x = np.array([0, np.max(x_data)])  # Extend line to y-axis
    fit_line_y = slope * fit_line_x + intercept

    return {
        'x_data': x_data,
        'y_data': y_data,
        'fit_line_x': fit_line_x,
        'fit_line_y': fit_line_y,
        'crystallite_size_A': crystallite_size,
        'strain': strain,
        'r_squared': r_value ** 2
    }


# =============================================================================
# Standalone Test Block
# =============================================================================
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    print("--- Testing microstructure.analysis.py ---")

    # --- Test 1: Scherrer calculation ---
    print("\n[Test 1] Scherrer Calculation")
    try:
        size = calculate_scherrer_size(peak_fwhm=0.5, peak_angle=30.0)
        # Expected: (0.9 * 1.5406) / (np.deg2rad(0.5) * np.cos(np.deg2rad(15)))
        expected_size = 164.46
        print(f"  Calculated size: {size:.2f} Å (Expected: ~{expected_size:.2f} Å)")
        assert np.isclose(size, expected_size, rtol=1e-3)
        print("  --> SUCCESS")
    except MicrostructureError as e:
        print(f"  --> FAILED: {e}")

    # --- Test 2: Williamson-Hall calculation ---
    print("\n[Test 2] Williamson-Hall Calculation")
    try:
        # Generate synthetic data with known properties
        true_size_A = 450.0  # Angstroms
        true_strain = 0.0015
        K = 0.9
        WAVELENGTH = 1.5406

        y_intercept = (K * WAVELENGTH) / true_size_A
        slope = true_strain

        # Create a set of realistic peak angles
        angles_2theta = np.array([20, 40, 60, 80])
        theta_rad = np.deg2rad(angles_2theta / 2.0)

        x_pts = 4 * np.sin(theta_rad)
        y_pts = slope * x_pts + y_intercept

        # Back-calculate the FWHM that would produce this W-H plot
        fwhm_rad = y_pts / np.cos(theta_rad)
        fwhm_deg = np.rad2deg(fwhm_rad)

        mock_peaks_df = pd.DataFrame({
            'angle': angles_2theta,
            'fwhm_angle': fwhm_deg
        })

        results = calculate_williamson_hall(mock_peaks_df)

        print(f"  Calculated Size: {results['crystallite_size_A']:.2f} Å (True: {true_size_A:.2f} Å)")
        print(f"  Calculated Strain: {results['strain']:.5f} (True: {true_strain:.5f})")
        print(f"  R-squared of fit: {results['r_squared']:.4f}")

        assert np.isclose(results['crystallite_size_A'], true_size_A)
        assert np.isclose(results['strain'], true_strain)
        assert results['r_squared'] > 0.9999

        # Test the plotting data
        plt.figure(figsize=(8, 6))
        plt.scatter(results['x_data'], results['y_data'], label='W-H Data Points')
        plt.plot(results['fit_line_x'], results['fit_line_y'], 'r-', label='Linear Fit')
        plt.title("Williamson-Hall Plot (Test)")
        plt.xlabel("4sin(θ)")
        plt.ylabel("βcos(θ)")
        plt.legend()
        plt.grid(True)
        plt.show()

        print("  --> SUCCESS")
    except MicrostructureError as e:
        print(f"  --> FAILED: {e}")

