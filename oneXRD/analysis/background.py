import numpy as np


# =============================================================================
# Custom Exception
# =============================================================================

class BackgroundError(Exception):
    """Custom exception for errors during background subtraction."""
    pass


# =============================================================================
# Background Subtraction Algorithms
# =============================================================================

def subtract_polynomial(angles, intensities, selected_indices, poly_order=3):
    """
    Calculates a background by fitting a polynomial to user-selected points.

    Args:
        angles (np.ndarray): The array of 2-theta angles.
        intensities (np.ndarray): The array of corresponding intensities.
        selected_indices (list[int]): A list of integer indices corresponding
                                      to points selected by the user.
        poly_order (int, optional): The order of the polynomial to fit.
                                    Defaults to 3.

    Returns:
        np.ndarray: An array of the calculated background values, with the
                    same shape as the input intensities.

    Raises:
        BackgroundError: If the number of selected points is less than or
                         equal to the polynomial order.
    """
    if len(selected_indices) <= poly_order:
        raise BackgroundError(f"Must select at least {poly_order + 1} points for a polynomial of order {poly_order}.")

    # Get the x and y values of the selected points
    selected_angles = angles[selected_indices]
    selected_intensities = intensities[selected_indices]

    # Fit the polynomial
    coeffs = np.polyfit(selected_angles, selected_intensities, poly_order)

    # Create the polynomial function
    p = np.poly1d(coeffs)

    # Calculate the background across the entire angle range
    background = p(angles)

    return background


def subtract_iterative_erosion(intensities, iterations=50):
    """
    Calculates a background using an iterative erosion method.

    This is often called a "rubber band" algorithm, as it's equivalent to
    stretching a rubber band under the data to separate peaks from the
    background. It's a simplified version of the SNIP algorithm.

    Args:
        intensities (np.ndarray): The array of intensity values.
        iterations (int, optional): The number of iterations to perform.
                                    More iterations result in a smoother,
                                    more aggressive background. Defaults to 50.

    Returns:
        np.ndarray: An array of the calculated background values.
    """
    background = np.copy(intensities)

    for _ in range(iterations):
        # Shift the array to get left and right neighbors
        shifted_left = np.roll(background, 1)
        shifted_right = np.roll(background, -1)

        # Take the average of the neighbors
        neighbors_avg = (shifted_left + shifted_right) / 2.0

        # The core of the algorithm: if a point is higher than the average
        # of its neighbors, pull it down.
        background = np.minimum(background, neighbors_avg)

    return background


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    print("--- Testing background.py ---")

    # --- 1. Generate realistic fake XRD data ---
    # A curved background (sine wave) with two Gaussian peaks
    angles = np.linspace(10, 80, 1000)
    true_background = 100 + 80 * np.sin((angles - 10) / 20) + (angles / 2)

    # Add Gaussian peaks
    peak1 = 500 * np.exp(-((angles - 30) ** 2) / (2 * 0.5 ** 2))
    peak2 = 800 * np.exp(-((angles - 55) ** 2) / (2 * 0.8 ** 2))

    raw_intensities = true_background + peak1 + peak2 + np.random.normal(0, 5, len(angles))

    # --- 2. Test Polynomial Method ---
    print("\n[Test 1] Polynomial Background Subtraction")
    try:
        # Simulate user picking points in the valleys
        selected_indices = [0, 200, 500, 750, 999]
        poly_background = subtract_polynomial(angles, raw_intensities, selected_indices, poly_order=4)

        plt.figure(figsize=(10, 6))
        plt.plot(angles, raw_intensities, label='Raw Data')
        plt.plot(angles, true_background, 'k--', label='True Background')
        plt.plot(angles[selected_indices], raw_intensities[selected_indices], 'ro', label='Selected Points')
        plt.plot(angles, poly_background, 'r-', label='Calculated Polynomial Background')
        plt.title("Test: Polynomial Background")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.show()
        print("  --> SUCCESS (Visual check: plot should look reasonable)")

    except BackgroundError as e:
        print(f"  --> FAILED: {e}")

    # --- 3. Test Iterative Erosion Method ---
    print("\n[Test 2] Iterative Erosion ('Rubber Band') Method")
    try:
        erosion_background = subtract_iterative_erosion(raw_intensities, iterations=100)

        plt.figure(figsize=(10, 6))
        plt.plot(angles, raw_intensities, label='Raw Data')
        plt.plot(angles, true_background, 'k--', label='True Background')
        plt.plot(angles, erosion_background, 'g-', label='Calculated Erosion Background')
        plt.title("Test: Iterative Erosion Background")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.show()
        print("  --> SUCCESS (Visual check: plot should look reasonable)")

    except Exception as e:
        print(f"  --> FAILED: {e}")

    # --- 4. Test Error Handling ---
    print("\n[Test 3] Polynomial Error Handling")
    try:
        # Try to fit a 4th order poly with only 3 points
        subtract_polynomial(angles, raw_intensities, [0, 100, 200], poly_order=4)
        print("  --> FAILED: Should have raised BackgroundError")
    except BackgroundError as e:
        print(f"  --> SUCCESS: Correctly caught error -> {e}")

