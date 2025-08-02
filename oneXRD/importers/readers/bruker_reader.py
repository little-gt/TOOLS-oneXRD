import numpy as np
import re
import os


# =============================================================================
# Custom Exception
# =============================================================================

class DataImportError(Exception):
    """Custom exception for errors during data file importing."""
    pass


# =============================================================================
# The Bruker RAW v4 Reader Module
# =============================================================================

def read_bruker_raw_v4(filepath):
    """
    Reads a Bruker RAW format version 4 binary file.

    This format typically has a text header containing metadata followed by
    a block of binary data for the intensities.

    Args:
        filepath (str): The full path to the .raw file.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two NumPy arrays:
                                       (angles, intensities).

    Raises:
        DataImportError: If the file is not a valid Bruker RAW v4 file,
                         is corrupted, or cannot be found.
    """
    try:
        with open(filepath, 'rb') as f:
            # The header is usually within the first 2048 bytes
            header_bytes = f.read(2048)
            # Decode using 'latin-1' which is robust for mixed text/binary
            header_text = header_bytes.decode('latin-1')

            # Use regex to find the required metadata
            start_match = re.search(r'START=\s*([0-9\.]+)', header_text)
            step_match = re.search(r'STEPSIZE=\s*([0-9\.]+)', header_text)
            count_match = re.search(r'COUNT=\s*([0-9]+)', header_text)

            if not all([start_match, step_match, count_match]):
                raise DataImportError(
                    "File is not a valid Bruker RAW v4 file. Missing essential metadata in the header.")

            start_angle = float(start_match.group(1))
            step_size = float(step_match.group(1))
            count = int(count_match.group(1))

            # The actual intensity data starts after the header block.
            # We assume the header is 2048 bytes, which is standard.
            f.seek(2048)

            # Read the binary intensity data as 32-bit floats
            intensities = np.fromfile(f, dtype=np.float32, count=count)

            if len(intensities) != count:
                raise DataImportError(
                    f"Data corruption: Header specified {count} points, but only {len(intensities)} could be read.")

            # Generate the corresponding angles array
            angles = np.arange(count, dtype=np.float32) * step_size + start_angle

            print(f"Successfully loaded Bruker RAW file: '{os.path.basename(filepath)}'")
            return angles, intensities

    except FileNotFoundError:
        raise DataImportError(f"File not found: {filepath}")
    except Exception as e:
        if isinstance(e, DataImportError):
            raise
        raise DataImportError(f"An unexpected error occurred while reading the Bruker file: {e}")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    print("--- Testing bruker_reader.py ---")

    # --- Test 1: Create a simulated valid .raw file and read it ---
    print("\n[Test 1] Simulated valid Bruker RAW v4 file")

    # Define metadata
    test_header_text = """
    FORMAT= RAW4
    DATE= 1-JAN-2024
    START= 10.0
    STEPSIZE= 0.02
    COUNT= 5
    """
    # Create a header of exactly 2048 bytes
    header_block = (test_header_text.ljust(2048)).encode('latin-1')

    # Create binary data
    test_intensities = np.array([100.0, 150.5, 2000.0, 140.2, 90.0], dtype=np.float32)
    data_block = test_intensities.tobytes()

    # Write the full simulated file
    file_path = "test_bruker.raw"
    try:
        with open(file_path, 'wb') as f:
            f.write(header_block)
            f.write(data_block)

        angles, intensities = read_bruker_raw_v4(file_path)

        # Verify the results
        assert len(angles) == 5
        assert len(intensities) == 5
        assert np.isclose(angles[0], 10.0)
        assert np.isclose(angles[4], 10.0 + 4 * 0.02)
        assert np.isclose(intensities[2], 2000.0)
        print("  --> SUCCESS")

    except DataImportError as e:
        print(f"  --> FAILED: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Test 2: Corrupted header ---
    print("\n[Test 2] Corrupted file (missing STEPSIZE)")
    bad_header_text = """
    FORMAT= RAW4
    START= 10.0
    COUNT= 5
    """
    bad_header_block = (bad_header_text.ljust(2048)).encode('latin-1')

    file_path = "test_bad_bruker.raw"
    try:
        with open(file_path, 'wb') as f:
            f.write(bad_header_block)
            f.write(data_block)  # use data from previous test

        read_bruker_raw_v4(file_path)
        print("  --> FAILED: Should have raised DataImportError")

    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught error -> {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Test 3: File not found ---
    print("\n[Test 3] File not found")
    try:
        read_bruker_raw_v4("non_existent_file.raw")
        print("  --> FAILED: Should have raised DataImportError")
    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught error -> {e}")
