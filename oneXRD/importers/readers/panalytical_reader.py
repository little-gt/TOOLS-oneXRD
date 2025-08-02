import numpy as np
import xml.etree.ElementTree as ET
import os


# =============================================================================
# Custom Exception
# =============================================================================

class DataImportError(Exception):
    """Custom exception for errors during data file importing."""
    pass


# =============================================================================
# The PANalytical XRDML Reader Module
# =============================================================================

def read_panalytical_xrdml(filepath):
    """
    Reads a PANalytical XRDML file (.xrdml).

    This format is XML-based. The function parses the XML tree to find the
    2-theta and intensity data arrays.

    Args:
        filepath (str): The full path to the .xrdml file.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two NumPy arrays:
                                       (angles, intensities).

    Raises:
        DataImportError: If the file cannot be parsed, is not a valid
                         XRDML file, or is corrupted.
    """
    try:
        # Register the namespace to make searching easier. The namespace is
        # usually defined at the root of the XRDML file.
        # We find it dynamically to be more robust.
        tree = ET.parse(filepath)
        root = tree.getroot()
        namespace = root.tag.split('}')[0].strip('{')
        ns = {'ns': namespace}

        # Find the scan data
        scan_node = root.find('.//ns:scan', ns)
        if scan_node is None:
            raise DataImportError("Could not find a <scan> element in the file.")

        # Extract data arrays. They are typically inside a 'dataPoints' element.
        data_points = scan_node.find('.//ns:dataPoints', ns)
        if data_points is None:
            raise DataImportError("Could not find a <dataPoints> element in the scan.")

        # Angles are in a <positions> tag, often with an 'axis' attribute.
        positions_node = data_points.find('.//ns:positions[@axis="2Theta"]', ns)
        if positions_node is None:
            raise DataImportError("Could not find <positions> for 2Theta axis.")

        # Intensities can be in <counts> or <intensities>
        intensities_node = data_points.find('.//ns:intensities', ns)
        if intensities_node is None:
            intensities_node = data_points.find('.//ns:counts', ns)

        if intensities_node is None:
            raise DataImportError("Could not find <intensities> or <counts> data.")

        # The data is space-separated text inside the tags
        angles_str = positions_node.text.strip()
        intensities_str = intensities_node.text.strip()

        angles = np.fromstring(angles_str, sep=' ', dtype=np.float64)
        intensities = np.fromstring(intensities_str, sep=' ', dtype=np.float64)

        if angles.size != intensities.size:
            raise DataImportError(
                "Data corruption: The number of angle points does not match the number of intensity points.")

        if angles.size == 0:
            raise DataImportError("No data points found in the file.")

        print(f"Successfully loaded PANalytical XRDML file: '{os.path.basename(filepath)}'")
        return angles, intensities

    except FileNotFoundError:
        raise DataImportError(f"File not found: {filepath}")
    except ET.ParseError:
        raise DataImportError(f"Failed to parse XML in '{os.path.basename(filepath)}'. The file may be corrupted.")
    except Exception as e:
        if isinstance(e, DataImportError):
            raise
        raise DataImportError(f"An unexpected error occurred: {e}")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    print("--- Testing panalytical_reader.py ---")

    # --- Test 1: Create and read a valid XRDML file ---
    print("\n[Test 1] Simulated valid XRDML file")

    # A simplified but structurally correct XRDML file content
    xrdml_data = """<?xml version="1.0" encoding="UTF-8"?>
<xrdMeasurements xmlns="http://www.panalytical.com/XRDML/1.0">
  <measurement>
    <scan>
      <dataPoints>
        <positions axis="2Theta" unit="deg">20.0 20.1 20.2</positions>
        <intensities unit="counts">500 1200 450</intensities>
      </dataPoints>
    </scan>
  </measurement>
</xrdMeasurements>
"""
    file_path = "test_panalytical.xrdml"
    try:
        with open(file_path, 'w') as f:
            f.write(xrdml_data)

        angles, intensities = read_panalytical_xrdml(file_path)

        assert len(angles) == 3
        assert np.isclose(angles[0], 20.0)
        assert np.isclose(intensities[1], 1200)
        print("  --> SUCCESS")

    except DataImportError as e:
        print(f"  --> FAILED: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Test 2: Malformed XML file ---
    print("\n[Test 2] Malformed XML file")
    malformed_data = "<xrdMeasurements><scan>... no closing tag"
    file_path = "test_malformed.xrdml"
    try:
        with open(file_path, 'w') as f:
            f.write(malformed_data)

        read_panalytical_xrdml(file_path)
        print("  --> FAILED: Should have raised DataImportError")

    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught XML parse error.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    # --- Test 3: File not found ---
    print("\n[Test 3] File not found")
    try:
        read_panalytical_xrdml("non_existent_file.xrdml")
        print("  --> FAILED: Should have raised DataImportError")
    except DataImportError as e:
        print(f"  --> SUCCESS: Correctly caught file not found error.")
