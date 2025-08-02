import os

# Import the specific reader functions from their modules
from .readers.generic_reader import read_generic_text_file, DataImportError
from .readers.bruker_reader import read_bruker_raw_v4
from .readers.cif_reader import read_cif_file
from .readers.panalytical_reader import read_panalytical_xrdml

# =============================================================================
# The Importer Engine
# =============================================================================

# A mapping of lower-case file extensions to their respective reader functions.
READER_MAPPING = {
    '.raw': read_bruker_raw_v4,
    '.xrdml': read_panalytical_xrdml,
    '.cif': read_cif_file,
    # Generic text formats are the fallback, but we can be explicit
    '.xy': read_generic_text_file,
    '.csv': read_generic_text_file,
    '.txt': read_generic_text_file,
}


def load_data(filepath):
    """
    Loads XRD data from a given file path, automatically determining the
    correct reader to use based on the file extension.

    This function serves as the main entry point for all file loading
    operations in the oneXRD application.

    Args:
        filepath (str): The path to the data file.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two NumPy arrays:
                                       (angles, intensities).

    Raises:
        DataImportError: If the file format is not supported, the file
                         is corrupted, or cannot be found.
    """
    if not os.path.exists(filepath):
        raise DataImportError(f"File not found: {filepath}")

    # Extract the file extension and convert to lowercase
    _, extension = os.path.splitext(filepath)
    extension = extension.lower()

    # Look up the appropriate reader function from the mapping
    reader_func = READER_MAPPING.get(extension)

    try:
        if reader_func:
            print(f"INFO: Found specific reader '{reader_func.__name__}' for extension '{extension}'")
            return reader_func(filepath)
        else:
            # If no specific reader is found, fall back to the generic text reader
            print(f"INFO: No specific reader for '{extension}'. Attempting generic text reader.")
            return read_generic_text_file(filepath)
    except DataImportError as e:
        # Re-raise the specific error from the reader to the calling UI
        raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise DataImportError(f"An unexpected error occurred while processing '{os.path.basename(filepath)}': {e}")


# =============================================================================
# Standalone Integration Test for the Entire Importer Package
# =============================================================================

if __name__ == '__main__':
    # This block now acts as an integration test for all our readers
    print("--- Testing Importer Engine ---")

    # We need to create dummy files for each reader to test the dispatching
    # Since we are inside a package, we need to handle paths carefully.
    # The dummy files are created in the current working directory.

    test_files_to_create = {
        'test.xy': '# Test data\n10 100\n11 110',
        'test.raw': None,  # Bruker .raw is binary, will be created specially
        'test.xrdml': '<?xml version="1.0"?><xrdMeasurements xmlns="http://www.panalytical.com/XRDML/1.0"><scan><dataPoints><positions axis="2Theta">20 21</positions><intensities>50 60</intensities></dataPoints></scan></xrdMeasurements>',
        'test.cif': "data_NaCl\n_cell_length_a 5.6\n_cell_length_b 5.6\n_cell_length_c 5.6\n_cell_angle_alpha 90\n_cell_angle_beta 90\n_cell_angle_gamma 90\nloop_\n_atom_site_label\n_atom_site_type_symbol\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z\nNa Na 0 0 0\nCl Cl 0.5 0.5 0.5",
        'test.dat': '30 300\n31 310'  # Test the fallback mechanism
    }

    # Special handling for Bruker binary file
    header = "START=10.0 STEPSIZE=0.1 COUNT=2".ljust(2048).encode('latin-1')
    import numpy as np

    data = np.array([100.0, 200.0], dtype=np.float32).tobytes()
    with open('test.raw', 'wb') as f:
        f.write(header)
        f.write(data)

    # Create the text-based files
    for filename, content in test_files_to_create.items():
        if content is not None:
            with open(filename, 'w') as f:
                f.write(content)

    # --- Run Tests ---
    all_files = list(test_files_to_create.keys())
    success_count = 0

    for filename in all_files:
        print(f"\n[Test] Loading '{filename}' with load_data()...")
        try:
            angles, intensities = load_data(filename)
            assert len(angles) > 0
            assert len(angles) == len(intensities)
            print("  --> SUCCESS")
            success_count += 1
        except DataImportError as e:
            # The CIF reader test might fail if pymatgen is not installed.
            if filename == 'test.cif' and 'Pymatgen' in str(e):
                print(f"  --> SKIPPED (Pymatgen not installed)")
            else:
                print(f"  --> FAILED: {e}")
        except Exception as e:
            print(f"  --> FAILED with unexpected error: {e}")

    # --- Test failure case ---
    print("\n[Test] Loading a non-existent file...")
    try:
        load_data("non_existent_file.xyz")
        print("  --> FAILED: Should have raised an error.")
    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught error -> {e}")
        success_count += 1

    print(f"\n--- Test Summary ---")
    # Add 1 to all_files count because of the extra failure test
    print(f"{success_count}/{len(all_files) + 1} tests passed or were correctly handled.")

    # --- Cleanup ---
    print("\nCleaning up test files...")
    for filename in all_files:
        if os.path.exists(filename):
            os.remove(filename)

