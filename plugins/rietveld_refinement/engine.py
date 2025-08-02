import os
import shutil
import tempfile
import numpy as np

# =============================================================================
# GSAS-II Dependency Check
# =============================================================================
try:
    import GSASIIscriptable as G2s

    GSASII_AVAILABLE = True
except ImportError:
    GSASII_AVAILABLE = False


# =============================================================================
# Custom Exception
# =============================================================================
class RietveldError(Exception):
    """Custom exception for Rietveld refinement errors."""
    pass


# =============================================================================
# The Rietveld Engine Class
# =============================================================================

class RietveldEngine:
    """A wrapper for performing Rietveld refinement using GSAS-II."""

    def __init__(self, api):
        """
        Args:
            api: The oneXRD PluginAPI object for logging.
        """
        if not GSASII_AVAILABLE:
            raise RietveldError(
                "GSAS-II is not installed or not found in the Python path. Please install it to use this feature.")
        self.api = api
        self.gpx = None
        self.temp_dir = tempfile.mkdtemp()
        self.hist = None
        self.phase = None

    def setup_refinement(self, exp_data_path, cif_file_path, phasename="MyPhase"):
        """
        Creates a new GSAS-II project and adds the experimental data and phase.

        Args:
            exp_data_path (str): Path to the experimental data file (e.g., .xy).
            cif_file_path (str): Path to the CIF file for the crystal structure.
            phasename (str): A name to assign to the phase.
        """
        gpx_path = os.path.join(self.temp_dir, "refinement.gpx")
        self.api.log(f"Creating GSAS-II project at: {gpx_path}")
        self.gpx = G2s.G2Project(gpxfile=gpx_path)

        self.api.log(f"Adding histogram: {exp_data_path}")
        self.hist = self.gpx.add_powder_histogram(exp_data_path, "XY")
        if not self.hist:
            raise RietveldError(f"Failed to load experimental data: {exp_data_path}")

        self.api.log(f"Adding phase: {cif_file_path}")
        self.phase = self.gpx.add_phase(cif_file_path, phasename=phasename, fmthint="CIF")
        if not self.phase:
            raise RietveldError(f"Failed to load CIF file: {cif_file_path}")

    def run_refinement(self, settings, cycles=5):
        """
        Configures and runs the refinement.

        Args:
            settings (dict): A dictionary of refinement settings.
                             Example: {'refine_cell': True, 'refine_background': True}
            cycles (int): The number of refinement cycles to perform.
        """
        if not self.gpx or not self.hist or not self.phase:
            raise RietveldError("Refinement has not been set up. Call setup_refinement() first.")

        ref_dict = {
            'Background': {'no.coeffs': 6, 'refine': settings.get('refine_background', True)},
            'Instrument Parameters': ['Scale', 'Zero'],  # Always refine these
            'Sample Parameters': ['DisplaceX', 'DisplaceY'],
        }

        if settings.get('refine_cell', True):
            ref_dict['Phase'] = ['Unit Cell']

        if settings.get('refine_peak_shape', True):
            # For a pseudo-voigt function
            ref_dict.setdefault('Peak Shape', []).extend(['U', 'V', 'W', 'X', 'Y'])

        self.api.log("Starting refinement...")
        self.gpx.set_refinement(ref_dict)
        self.gpx.refine(cycles=cycles)
        self.api.log("Refinement complete.")

    def get_results(self):
        """
        Extracts key results and data for plotting after refinement.

        Returns:
            dict: A dictionary containing results like 'rwp', 'chi2',
                  'refined_params', and arrays for plotting ('x', 'y_obs', etc.).
        """
        if not self.gpx:
            raise RietveldError("No project loaded.")

        results_dict = self.hist.get_results()
        plot_data = self.hist.get_plottable()

        final_results = {
            'rwp': results_dict.get('Rwp', 0.0),
            'chi2': results_dict.get('chi**2', 0.0),
            'refined_params': self.phase.get_refined_params(),
            'x': plot_data.get('x', []),
            'y_obs': plot_data.get('y', []),
            'y_calc': plot_data.get('ycalc', []),
            'y_bkg': plot_data.get('bkg', []),
            'y_diff': plot_data.get('y-ycalc', [])
        }
        return final_results

    def cleanup(self):
        """Deletes the temporary directory and all GSAS-II files."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.api.log(f"Cleaned up temporary directory: {self.temp_dir}")


# =============================================================================
# Standalone Test Block
# =============================================================================
if __name__ == '__main__':
    import matplotlib.pyplot as plt

    if not GSASII_AVAILABLE:
        print("Skipping RietveldEngine test: GSAS-II not found.")
    else:
        print("--- Testing RietveldEngine ---")


        # --- Mockups and Test Data Setup ---
        class MockAPI:
            def log(self, msg): print(f"API_LOG: {msg}")


        # Create a fake CIF file for NaCl
        nacl_cif = """
data_NaCl
_symmetry_space_group_name_H-M   'F m -3 m'
_cell_length_a   5.640
_cell_length_b   5.640
_cell_length_c   5.640
_cell_angle_alpha   90
_cell_angle_beta    90
_cell_angle_gamma   90
loop_
_atom_site_label _atom_site_type_symbol _atom_site_fract_x _atom_site_fract_y _atom_site_fract_z
Na Na 0 0 0
Cl Cl 0.5 0.5 0.5
"""
        test_cif_path = "test_nacl.cif"
        with open(test_cif_path, "w") as f:
            f.write(nacl_cif)

        # Create a fake experimental data file by calculating the pattern and adding noise
        from oneXRD.importers.readers.cif_reader import read_cif_file

        angles, intensities = read_cif_file(test_cif_path)
        noise = np.random.normal(0, np.sqrt(intensities) / 2, size=intensities.shape)
        noisy_intensities = intensities + noise
        test_xy_path = "test_data.xy"
        np.savetxt(test_xy_path, np.column_stack([angles, noisy_intensities]))

        # --- Run the Test ---
        engine = None
        try:
            print("\n[Test 1] Running full refinement workflow...")
            engine = RietveldEngine(MockAPI())
            engine.setup_refinement(test_xy_path, test_cif_path)

            settings = {'refine_cell': True, 'refine_background': True, 'refine_peak_shape': True}
            engine.run_refinement(settings, cycles=6)

            results = engine.get_results()

            print("\n--- Refinement Results ---")
            print(f"  Rwp: {results['rwp']:.4f}%")
            print(f"  chi^2: {results['chi2']:.4f}")
            print(f"  Refined Cell Parameter (a): {results['refined_params']['Cell'][0]:.4f} Å")

            assert results['rwp'] > 0 and results['rwp'] < 20  # Should be a reasonable value
            assert len(results['x']) == len(results['y_obs'])

            # --- Plotting Test ---
            print("\n[Test 2] Plotting results...")
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
            ax1.plot(results['x'], results['y_obs'], 'b.', label='Observed Data')
            ax1.plot(results['x'], results['y_calc'], 'r-', label='Calculated Pattern')
            ax1.plot(results['x'], results['y_bkg'], 'g--', label='Background')
            ax1.set_ylabel("Intensity")
            ax1.legend()

            ax2.plot(results['x'], results['y_diff'], 'k-')
            ax2.axhline(0, color='r', linestyle='--')
            ax2.set_xlabel("Angle (2θ)")
            ax2.set_ylabel("Difference")

            plt.tight_layout()
            plt.show()

            print("  --> SUCCESS (Visual check complete)")

        except RietveldError as e:
            print(f"  --> FAILED: {e}")
        finally:
            if engine:
                engine.cleanup()
            if os.path.exists(test_cif_path): os.remove(test_cif_path)
            if os.path.exists(test_xy_path): os.remove(test_xy_path)