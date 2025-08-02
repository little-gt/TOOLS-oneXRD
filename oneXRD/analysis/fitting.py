import numpy as np
import pandas as pd
from scipy.optimize import curve_fit


# =============================================================================
# Custom Exception
# =============================================================================

class FittingError(Exception):
    """Custom exception for errors during peak fitting."""
    pass


# =============================================================================
# Peak Profile Models
# =============================================================================

def _gaussian(x, amplitude, center, sigma):
    """Gaussian peak profile."""
    return amplitude * np.exp(-(x - center) ** 2 / (2 * sigma ** 2))


def _lorentzian(x, amplitude, center, gamma):
    """Lorentzian peak profile."""
    return amplitude * (gamma ** 2 / ((x - center) ** 2 + gamma ** 2))


def _pseudo_voigt(x, amplitude, center, fwhm, mixing):
    """
    Pseudo-Voigt peak profile.
    A linear combination of Gaussian and Lorentzian profiles.
    'mixing' (eta) = 0 for pure Gaussian, 1 for pure Lorentzian.
    """
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))  # FWHM to sigma for Gaussian
    gamma = fwhm / 2  # FWHM to HWHM (gamma) for Lorentzian
    return (1 - mixing) * _gaussian(x, amplitude, center, sigma) + mixing * _lorentzian(x, amplitude, center, gamma)


# Dictionary to map model names to functions
MODELS = {
    'gaussian': _gaussian,
    'lorentzian': _lorentzian,
    'pseudo_voigt': _pseudo_voigt
}


# =============================================================================
# Main Peak Fitting Function
# =============================================================================

def fit_peak(angles, intensities, peak_info, model_name='pseudo_voigt', fit_window_fwhm=3):
    """
    Fits a selected model to a single peak in the XRD data.

    Args:
        angles (np.ndarray): The full array of 2-theta angles.
        intensities (np.ndarray): The full array of intensities (background-subtracted).
        peak_info (pd.Series or dict): A row from the peak DataFrame containing
                                     at least 'angle', 'intensity', and 'fwhm_angle'.
        model_name (str, optional): The model to use for fitting.
                                    Options: 'gaussian', 'lorentzian', 'pseudo_voigt'.
                                    Defaults to 'pseudo_voigt'.
        fit_window_fwhm (float, optional): The width of the data window to use
                                           for fitting, as a multiple of the
                                           peak's FWHM. Defaults to 3.

    Returns:
        tuple[dict, np.ndarray]: A tuple containing:
            - A dictionary of the optimized fit parameters.
            - A NumPy array of the calculated fit curve over the window.
    """
    if model_name not in MODELS:
        raise FittingError(f"Model '{model_name}' not recognized. Available models: {list(MODELS.keys())}")

    # --- 1. Isolate the data window around the peak ---
    center_angle = peak_info['angle']
    fwhm = peak_info['fwhm_angle']
    window_half_width = fwhm * fit_window_fwhm / 2

    window_mask = (angles >= center_angle - window_half_width) & (angles <= center_angle + window_half_width)
    x_window = angles[window_mask]
    y_window = intensities[window_mask]

    if len(x_window) < 5:  # Need enough points to fit
        raise FittingError("Not enough data points in the selected window to perform a fit.")

    # --- 2. Set initial parameter guesses (p0) ---
    model_func = MODELS[model_name]
    if model_name == 'pseudo_voigt':
        # p0 = [amplitude, center, fwhm, mixing]
        p0 = [peak_info['intensity'], center_angle, fwhm, 0.5]
    elif model_name == 'gaussian':
        # p0 = [amplitude, center, sigma]
        sigma_guess = fwhm / (2 * np.sqrt(2 * np.log(2)))
        p0 = [peak_info['intensity'], center_angle, sigma_guess]
    elif model_name == 'lorentzian':
        # p0 = [amplitude, center, gamma]
        gamma_guess = fwhm / 2
        p0 = [peak_info['intensity'], center_angle, gamma_guess]

    # --- 3. Perform the curve fit ---
    try:
        popt, _ = curve_fit(model_func, x_window, y_window, p0=p0)
    except RuntimeError:
        raise FittingError("Optimal parameters not found. The fit did not converge.")

    # --- 4. Package the results ---
    fit_curve = model_func(x_window, *popt)
    fit_params = {}
    if model_name == 'pseudo_voigt':
        fit_params = {'amplitude': popt[0], 'center': popt[1], 'fwhm': popt[2], 'mixing': popt[3]}
    elif model_name == 'gaussian':
        fit_params = {'amplitude': popt[0], 'center': popt[1], 'sigma': popt[2]}
    elif model_name == 'lorentzian':
        fit_params = {'amplitude': popt[0], 'center': popt[1], 'gamma': popt[2]}

    return fit_params, x_window, fit_curve


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    print("--- Testing fitting.py ---")

    # --- 1. Generate realistic fake data for a single peak ---
    angles = np.linspace(25, 35, 1000)
    true_center = 30.0
    true_amplitude = 1000
    true_fwhm = 0.5
    true_mixing = 0.3  # A realistic mix of Gaussian and Lorentzian

    intensities = _pseudo_voigt(angles, true_amplitude, true_center, true_fwhm, true_mixing)
    intensities += np.random.normal(0, 20, len(angles))  # Add noise

    # --- 2. Simulate input from the peak_finding module ---
    # In a real scenario, these would come from the peaks_df DataFrame
    estimated_peak_info = pd.Series({
        'angle': 29.95,  # A slightly off estimate
        'intensity': 980,  # A slightly off estimate
        'fwhm_angle': 0.6  # A slightly off estimate
    })

    # --- 3. Test fitting with different models ---
    models_to_test = ['gaussian', 'pseudo_voigt']

    plt.figure(figsize=(12, 8))
    plt.plot(angles, intensities, '.', label='Raw Noisy Data')

    for model in models_to_test:
        print(f"\n[Test] Fitting with '{model}' model...")
        try:
            params, x_fit, y_fit = fit_peak(angles, intensities, estimated_peak_info, model_name=model)

            print("  Optimized Parameters:")
            for key, val in params.items():
                print(f"    {key}: {val:.4f}")

            plt.plot(x_fit, y_fit, '-', lw=2, label=f'Fitted {model.capitalize()}')
            print("  --> SUCCESS")

        except FittingError as e:
            print(f"  --> FAILED: {e}")

    plt.axvline(true_center, color='k', linestyle='--', label='True Center')
    plt.title("Peak Fitting Test")
    plt.xlabel("Angle (2-Theta)")
    plt.ylabel("Intensity")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.show()

