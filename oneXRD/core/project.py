import os
from .xrd_data import XRDData  # Use relative import within the same package


class Project:
    """
    Manages the entire session state, including the active experimental
    data and any loaded reference patterns.
    """

    def __init__(self):
        """Initializes a new, empty project."""
        self.db_id = None
        self.experimental_data = None
        self.reference_data = {}  # Dict to store references by display_name

    @property
    def has_experimental_data(self):
        """Returns True if experimental data is loaded."""
        return self.experimental_data is not None

    def load_experimental_data(self, xrd_data_obj, db_id=None):
        """
        Loads a new experimental pattern into the project.

        Args:
            xrd_data_obj (XRDData): The XRDData object for the experimental pattern.
            db_id (int, optional): The database ID if loaded from the database.
                                   Defaults to None.
        """
        if xrd_data_obj.is_reference:
            raise ValueError("Cannot load a reference pattern as experimental data.")
        self.experimental_data = xrd_data_obj
        self.db_id = db_id
        print(f"INFO: Loaded experimental data '{xrd_data_obj.display_name}' into project.")

    def add_reference(self, xrd_data_obj):
        """
        Adds a reference pattern to the project.

        Args:
            xrd_data_obj (XRDData): The XRDData object for the reference pattern.
        """
        if not xrd_data_obj.is_reference:
            raise ValueError("Can only add reference patterns (is_reference=True) here.")
        name = xrd_data_obj.display_name
        self.reference_data[name] = xrd_data_obj
        print(f"INFO: Added reference '{name}' to project.")

    def get_reference_by_name(self, name):
        """Retrieves a reference pattern by its display name."""
        return self.reference_data.get(name)

    def remove_reference(self, name):
        """Removes a reference pattern from the project."""
        if name in self.reference_data:
            del self.reference_data[name]
            print(f"INFO: Removed reference '{name}' from project.")
            return True
        return False

    def clear_project(self):
        """Resets the project to its initial empty state."""
        self.__init__()  # Re-initialize the object
        print("INFO: Project has been cleared.")

    def __repr__(self):
        """String representation for debugging."""
        exp_name = self.experimental_data.display_name if self.has_experimental_data else "None"
        num_refs = len(self.reference_data)
        return f"<Project | Experiment: '{exp_name}' | References: {num_refs}>"


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    import numpy as np

    print("--- Testing Project class ---")

    # --- 1. Initialization ---
    print("\n[Test 1] Initializing an empty project...")
    proj = Project()
    assert not proj.has_experimental_data
    assert not proj.reference_data
    assert proj.db_id is None
    print(f"  Initial state: {proj}")
    print("  --> SUCCESS")

    # --- 2. Load Experimental Data ---
    print("\n[Test 2] Loading experimental data...")
    exp_data = XRDData(np.array([1, 2]), np.array([3, 4]), filename="exp1.xy")
    proj.load_experimental_data(exp_data, db_id=42)
    assert proj.has_experimental_data
    assert proj.experimental_data.display_name == "exp1.xy"
    assert proj.db_id == 42
    print(f"  State after loading exp: {proj}")
    print("  --> SUCCESS")

    # --- 3. Add Reference Data ---
    print("\n[Test 3] Adding reference patterns...")
    ref1 = XRDData(np.array([5, 6]), np.array([7, 8]), filename="NaCl.cif", is_reference=True)
    ref2 = XRDData(np.array([9, 10]), np.array([11, 12]), filename="Quartz.cif", is_reference=True)
    proj.add_reference(ref1)
    proj.add_reference(ref2)
    assert len(proj.reference_data) == 2
    assert "NaCl.cif (Ref)" in proj.reference_data
    print(f"  State after adding refs: {proj}")
    print("  --> SUCCESS")

    # --- 4. Get and Remove a Reference ---
    print("\n[Test 4] Getting and removing a reference...")
    retrieved_ref = proj.get_reference_by_name("Quartz.cif (Ref)")
    assert retrieved_ref is not None
    assert np.array_equal(retrieved_ref.raw_angles, np.array([9, 10]))

    proj.remove_reference("NaCl.cif (Ref)")
    assert len(proj.reference_data) == 1
    assert proj.get_reference_by_name("NaCl.cif (Ref)") is None
    print(f"  State after removal: {proj}")
    print("  --> SUCCESS")

    # --- 5. Clear Project ---
    print("\n[Test 5] Clearing the project...")
    proj.clear_project()
    assert not proj.has_experimental_data
    assert not proj.reference_data
    assert proj.db_id is None
    print(f"  State after clearing: {proj}")
    print("  --> SUCCESS")

    # --- 6. Test ValueErrors ---
    print("\n[Test 6] Testing error handling...")
    try:
        proj.load_experimental_data(ref1)  # Should fail
        print("  --> FAILED: Should have raised ValueError")
    except ValueError:
        print("  --> SUCCESS: Correctly caught loading ref as exp.")

    try:
        proj.add_reference(exp_data)  # Should fail
        print("  --> FAILED: Should have raised ValueError")
    except ValueError:
        print("  --> SUCCESS: Correctly caught adding exp as ref.")
