import numpy as np
import os

# =============================================================================
# Dependency Check
# =============================================================================
# This module requires the 'pymatgen' library to function.
try:
    from pymatgen.core.structure import Structure
    from pymatgen.analysis.diffraction.xrd import XRDCalculator

    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False


# =============================================================================
# Custom Exception
# =============================================================================

class DataImportError(Exception):
    """Custom exception for errors during data file importing."""
    pass


# =============================================================================
# The CIF Reader and XRD Pattern Calculator Module
# =============================================================================

def read_cif_file(filepath, wavelength='CuKa'):
    """
    Reads a Crystallographic Information File (.cif) and calculates its
    theoretical powder XRD pattern.

    This function relies on the Pymatgen library.

    Args:
        filepath (str): The full path to the .cif file.
        wavelength (str, optional): The X-ray wavelength to use for the
                                    calculation. Defaults to 'CuKa'.
                                    Examples: 'CuKa', 'MoKa', 'CrKa'.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing two NumPy arrays:
                                       (2-theta angles, relative intensities).

    Raises:
        DataImportError: If pymatgen is not installed, or if the CIF file
                         cannot be parsed.
    """
    if not PYMATGEN_AVAILABLE:
        raise DataImportError(
            "The Pymatgen library is required to read CIF files. Please install it: 'pip install pymatgen'")

    try:
        # Load the crystal structure from the CIF file
        structure = Structure.from_file(filepath)

        # Initialize the XRD calculator with the specified wavelength
        calculator = XRDCalculator(wavelength=wavelength)

        # Calculate the diffraction pattern
        # scaled=True normalizes the max intensity to 100
        pattern = calculator.get_pattern(structure, scaled=True)

        # Extract the 2-theta angles and intensities
        angles = np.array(pattern.x)
        intensities = np.array(pattern.y)

        print(f"Successfully calculated pattern from: '{os.path.basename(filepath)}'")
        return angles, intensities

    except FileNotFoundError:
        raise DataImportError(f"File not found: {filepath}")
    except Exception as e:
        # Catch errors from pymatgen's parser
        raise DataImportError(f"Failed to parse CIF file '{os.path.basename(filepath)}'. Error: {e}")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    print("--- Testing cif_reader.py ---")

    if not PYMATGEN_AVAILABLE:
        print("\n[INFO] Pymatgen library not found. Skipping tests for cif_reader.py.")

    else:
        # --- Test 1: Create and read a valid CIF file (NaCl) ---
        print("\n[Test 1] Valid NaCl CIF file")

        # A standard CIF block for Sodium Chloride (NaCl)
        nacl_cif_data = """
data_NaCl
_symmetry_space_group_name_H-M   'F m -3 m'
_cell_length_a   5.6402
_cell_length_b   5.6402
_cell_length_c   5.6402
_cell_angle_alpha   90
_cell_angle_beta    90
_cell_angle_gamma   90

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Na   Na   0.00000   0.00000   0.00000
Cl   Cl   0.50000   0.50000   0.50000
"""
        file_path = "test_nacl.cif"
        try:
            with open(file_path, 'w') as f:
                f.write(nacl_cif_data)

            angles, intensities = read_cif_file(file_path)

            # Assertions to verify the result
            assert len(angles) > 0
            assert len(angles) == len(intensities)
            assert intensities.max() == 100.0  # scaled=True ensures this

            # Check for a known strong peak for NaCl (220 reflection)
            # Should be around 45.4 degrees 2-theta for CuKa
            known_peak_angle = 45.4
            # Find the index of the angle closest to our known peak
            closest_angle_idx = np.argmin(np.abs(angles - known_peak_angle))

            # Assert that the closest calculated peak is within a reasonable tolerance
            assert abs(angles[closest_angle_idx] - known_peak_angle) < 0.2

            print("  --> SUCCESS")

        except DataImportError as e:
            print(f"  --> FAILED: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

        # --- Test 2: Malformed CIF file ---
        print("\n[Test 2] Malformed CIF file")
        malformed_cif_data = "this is not a valid cif file"
        file_path = "test_malformed.cif"
        try:
            with open(file_path, 'w') as f:
                f.write(malformed_cif_data)

            read_cif_file(file_path)
            print("  --> FAILED: Should have raised DataImportError")

        except DataImportError as e:
            print(f"  --> SUCCESS: Correctly caught error.")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

