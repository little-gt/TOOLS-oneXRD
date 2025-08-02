import numpy as np
import io
import os


# =============================================================================
# Custom Exception
# =============================================================================

class DataImportError(Exception):
    """Custom exception for errors during data file importing."""
    pass


# =============================================================================
# The Generic Reader Module
# =============================================================================

def read_generic_text_file(filepath):
    """
    Reads a generic 2-column text file containing XRD data.

    This function is designed to be robust and attempts to parse files with
    common delimiters (whitespace, comma, tab) and can automatically skip
    header lines that are common in scientific data files.

    Args:
        filepath (str): The full path to the data file.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two NumPy arrays:
                                       (angles, intensities).

    Raises:
        DataImportError: If the file cannot be read, is empty, or cannot be
                         parsed into two columns of numeric data.
    """
    try:
        # First, find the first line with actual data to intelligently
        # determine the number of header rows to skip.
        header_rows = 0
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                line = line.strip()
                # Skip empty lines or common comment characters
                if not line or line.startswith(('#', '!', '/', ' ')):
                    header_rows = i + 1
                    continue
                # We've found the first potential data line, so stop.
                break

        # Try loading with different common delimiters
        for delimiter in [None, ',', '\t']:  # None handles any whitespace
            try:
                data = np.loadtxt(filepath, skiprows=header_rows, delimiter=delimiter)

                # Check if data has at least 2 columns
                if data.ndim == 2 and data.shape[1] >= 2:
                    print(
                        f"Successfully loaded '{os.path.basename(filepath)}' with delimiter: '{'whitespace' if delimiter is None else delimiter}'")
                    angles = data[:, 0]
                    intensities = data[:, 1]

                    # Ensure data is not empty
                    if angles.size == 0:
                        raise DataImportError("File contains no data points.")

                    return angles, intensities

            except (ValueError, IndexError):
                # This delimiter didn't work, try the next one
                continue

        # If all delimiters failed, raise an error
        raise DataImportError("Could not parse file. Ensure it is a valid 2-column numeric text file.")

    except FileNotFoundError:
        raise DataImportError(f"File not found: {filepath}")
    except Exception as e:
        # Catch any other unexpected errors during file processing
        if isinstance(e, DataImportError):
            raise  # Re-raise our specific error
        raise DataImportError(f"An unexpected error occurred: {e}")


# =============================================================================
# Standalone Test Block (Corrected Version)
# =============================================================================

if __name__ == '__main__':
    print("--- Testing generic_reader.py (Corrected) ---")

    test_files = []  # Keep track of created files to clean up

    # --- Test 1: Space-delimited file with header ---
    print("\n[Test 1] Space-delimited file with header")
    space_delim_data = """# Test XRD Data
# Format: 2-Theta Intensity
10.0  150.5
10.1  200.0
10.2  180.2
"""
    file_path = "non_existent_file.xy"
    test_files.append(file_path)
    try:
        with open(file_path, "w") as f:
            f.write(space_delim_data)

        angles, intensities = read_generic_text_file(file_path)
        assert len(angles) == 3
        assert angles[0] == 10.0
        assert intensities[1] == 200.0
        print("  --> SUCCESS")
    except DataImportError as e:
        print(f"  --> FAILED: {e}")

    # --- Test 2: Comma-separated file (.csv) ---
    print("\n[Test 2] Comma-separated file")
    csv_data = "20.5,500\n20.6,520\n20.7,550"
    file_path = "test.csv"
    test_files.append(file_path)
    try:
        with open(file_path, "w") as f:
            f.write(csv_data)

        angles, intensities = read_generic_text_file(file_path)
        assert len(angles) == 3
        assert angles[1] == 20.6
        assert intensities[2] == 550
        print("  --> SUCCESS")
    except DataImportError as e:
        print(f"  --> FAILED: {e}")

    # --- Test 3: Corrupted file with text in data ---
    print("\n[Test 3] Corrupted file")
    corrupted_data = "30.0  1000\n30.1  BAD_DATA\n30.2  1100"
    file_path = "test_corrupted.txt"
    test_files.append(file_path)
    try:
        with open(file_path, "w") as f:
            f.write(corrupted_data)

        read_generic_text_file(file_path)
        print("  --> FAILED: Should have raised DataImportError")
    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught error -> {e}")

    # --- Test 4: File not found ---
    print("\n[Test 4] File not found")
    try:
        # THIS IS THE ACTUAL TEST for file not found
        read_generic_text_file("non_existent_file.xy")
        print("  --> FAILED: Should have raised DataImportError")
    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught error -> {e}")
    finally:
        # --- Cleanup ---
        print("\nCleaning up test files...")
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)
        print("Cleanup complete.")
