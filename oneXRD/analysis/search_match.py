import numpy as np
import pandas as pd


# =============================================================================
# Custom Exception
# =============================================================================

class SearchMatchError(Exception):
    """Custom exception for errors during the search-match process."""
    pass


# =============================================================================
# Search-Match Function
# =============================================================================

def perform_search_match(experimental_peaks, reference_pattern, angle_tolerance):
    """
    Compares experimental peaks against a reference pattern to find matches.

    Args:
        experimental_peaks (pd.DataFrame): DataFrame of found experimental peaks.
                                           Must contain an 'angle' column.
        reference_pattern (pd.DataFrame): DataFrame of a theoretical reference pattern.
                                          Must contain 'angle' and 'intensity' columns.
        angle_tolerance (float): The 2-theta window to consider a peak a match
                                 (e.g., 0.1 degrees).

    Returns:
        tuple[float, pd.DataFrame]: A tuple containing:
            - figure_of_merit (float): A score from 0-100 indicating the
                                       quality of the match.
            - match_results (pd.DataFrame): A DataFrame detailing the matches.
    """
    if not all(col in experimental_peaks.columns for col in ['angle']):
        raise SearchMatchError("Experimental peaks DataFrame must contain 'angle' column.")
    if not all(col in reference_pattern.columns for col in ['angle', 'intensity']):
        raise SearchMatchError("Reference pattern DataFrame must contain 'angle' and 'intensity' columns.")

    if reference_pattern.empty:
        return 0.0, pd.DataFrame()

    # Sort reference pattern by intensity (descending) to prioritize strong peaks
    reference_pattern = reference_pattern.sort_values(by='intensity', ascending=False).reset_index(drop=True)

    matched_peaks_info = []
    total_reference_intensity = reference_pattern['intensity'].sum()
    matched_reference_intensity = 0.0

    # Keep track of used experimental peaks to prevent one peak from matching multiple references
    used_exp_indices = set()

    for ref_idx, ref_peak in reference_pattern.iterrows():
        ref_angle = ref_peak['angle']
        ref_intensity = ref_peak['intensity']

        # Define the search window
        min_angle = ref_angle - angle_tolerance
        max_angle = ref_angle + angle_tolerance

        # Find potential matches in the experimental data within the window
        potential_matches = experimental_peaks[
            (experimental_peaks['angle'] >= min_angle) &
            (experimental_peaks['angle'] <= max_angle)
            ]

        # Exclude already used experimental peaks
        potential_matches = potential_matches[~potential_matches.index.isin(used_exp_indices)]

        if not potential_matches.empty:
            # Find the closest experimental peak within the window
            closest_match = potential_matches.iloc[(potential_matches['angle'] - ref_angle).abs().argmin()]

            # Mark this experimental peak as used
            used_exp_indices.add(closest_match.name)

            # Add to our list of successful matches
            matched_peaks_info.append({
                'exp_angle': closest_match['angle'],
                'ref_angle': ref_angle,
                'ref_intensity': ref_intensity,
                'delta_angle': closest_match['angle'] - ref_angle
            })

            # Add the intensity of this matched reference peak to our running total
            matched_reference_intensity += ref_intensity

    if not matched_peaks_info:
        return 0.0, pd.DataFrame()

    # Calculate the Figure of Merit (FOM)
    # This score is the percentage of total reference intensity that was matched.
    figure_of_merit = (matched_reference_intensity / total_reference_intensity) * 100.0

    match_results_df = pd.DataFrame(matched_peaks_info)

    return figure_of_merit, match_results_df


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    print("--- Testing search_match.py ---")

    # --- 1. Define a reference pattern (e.g., for NaCl) ---
    reference_pattern = pd.DataFrame({
        'angle': [31.7, 45.5, 56.5],
        'intensity': [100.0, 80.0, 60.0]  # Total intensity = 240
    })

    # --- 2. Test Case 1: Good Match ---
    print("\n[Test 1] Good Match Scenario")
    # Experimental peaks include all reference peaks + one impurity
    good_exp_peaks = pd.DataFrame({
        'angle': [31.75, 40.0, 45.48, 56.52],  # Impurity at 40.0
        'intensity': [950, 50, 750, 550]
    })

    fom, results = perform_search_match(good_exp_peaks, reference_pattern, angle_tolerance=0.1)
    print(f"  Figure of Merit: {fom:.2f}%")
    print("  Match Results:")
    print(results)
    assert fom == 100.0
    assert len(results) == 3
    print("  --> SUCCESS")

    # --- 3. Test Case 2: Poor Match ---
    print("\n[Test 2] Poor Match Scenario")
    # Experimental peaks are completely different
    poor_exp_peaks = pd.DataFrame({
        'angle': [20.0, 25.0, 50.0],
        'intensity': [1000, 800, 600]
    })

    fom, results = perform_search_match(poor_exp_peaks, reference_pattern, angle_tolerance=0.1)
    print(f"  Figure of Merit: {fom:.2f}%")
    print("  Match Results:")
    print(results)
    assert fom == 0.0
    assert results.empty
    print("  --> SUCCESS")

    # --- 4. Test Case 3: Partial Match ---
    print("\n[Test 3] Partial Match Scenario")
    # The strongest peak is missing from the experimental data
    partial_exp_peaks = pd.DataFrame({
        'angle': [45.51, 56.49],
        'intensity': [820, 610]
    })

    fom, results = perform_search_match(partial_exp_peaks, reference_pattern, angle_tolerance=0.1)
    expected_fom = ((80.0 + 60.0) / 240.0) * 100.0
    print(f"  Figure of Merit: {fom:.2f}% (Expected: {expected_fom:.2f}%)")
    print("  Match Results:")
    print(results)
    assert np.isclose(fom, expected_fom)
    assert len(results) == 2
    print("  --> SUCCESS")

