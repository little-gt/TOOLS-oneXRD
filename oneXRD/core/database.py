import sqlite3
import numpy as np
import pandas as pd
import json
import zlib
import os


# =============================================================================
# Custom Exception
# =============================================================================

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


# =============================================================================
# Helper Functions for Data Serialization
# =============================================================================

def _serialize_array(arr):
    """Compresses a NumPy array into a binary object for database storage."""
    return zlib.compress(arr.tobytes())


def _deserialize_array(blob, dtype=np.float64):
    """Decompresses a binary object from the database into a NumPy array."""
    return np.frombuffer(zlib.decompress(blob), dtype=dtype)


# =============================================================================
# Database Manager Class
# =============================================================================

class DatabaseManager:
    def __init__(self, db_path):
        """
        Initializes the DatabaseManager.

        Args:
            db_path (str): The path to the SQLite database file.
                           Use ':memory:' for an in-memory database for testing.
        """
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        """Returns a new database connection."""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Creates the necessary database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS experiments
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               sample_name
                               TEXT
                               NOT
                               NULL,
                               timestamp
                               DATETIME
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               notes
                               TEXT
                           )
                           """)
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS raw_data
                           (
                               experiment_id
                               INTEGER,
                               angles
                               BLOB
                               NOT
                               NULL,
                               intensities
                               BLOB
                               NOT
                               NULL,
                               FOREIGN
                               KEY
                           (
                               experiment_id
                           ) REFERENCES experiments
                           (
                               id
                           )
                               )
                           """)
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS analysis_results
                           (
                               experiment_id
                               INTEGER
                               UNIQUE,
                               peaks_df_json
                               TEXT,
                               background_subtracted_intensities
                               BLOB,
                               FOREIGN
                               KEY
                           (
                               experiment_id
                           ) REFERENCES experiments
                           (
                               id
                           )
                               )
                           """)
            conn.commit()

    def add_experiment(self, sample_name, angles, intensities, notes=""):
        """Adds a new experiment and its raw data to the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Add to experiments table
                cursor.execute("INSERT INTO experiments (sample_name, notes) VALUES (?, ?)", (sample_name, notes))
                experiment_id = cursor.lastrowid

                # Add to raw_data table
                s_angles = _serialize_array(angles)
                s_intensities = _serialize_array(intensities)
                cursor.execute("INSERT INTO raw_data (experiment_id, angles, intensities) VALUES (?, ?, ?)",
                               (experiment_id, s_angles, s_intensities))
                conn.commit()
                return experiment_id
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to add experiment: {e}")

    def update_analysis_results(self, experiment_id, peaks_df, bg_sub_intensities):
        """Adds or updates the analysis results for a given experiment."""
        peaks_json = peaks_df.to_json(orient='split')
        s_bg_intensities = _serialize_array(bg_sub_intensities)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                               INSERT INTO analysis_results (experiment_id, peaks_df_json, background_subtracted_intensities)
                               VALUES (?, ?, ?) ON CONFLICT(experiment_id) DO
                               UPDATE SET
                                   peaks_df_json=excluded.peaks_df_json,
                                   background_subtracted_intensities=excluded.background_subtracted_intensities
                               """, (experiment_id, peaks_json, s_bg_intensities))
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to update results: {e}")

    def get_experiment_data(self, experiment_id):
        """Retrieves all data for a single experiment."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch experiment metadata
            cursor.execute("SELECT sample_name, timestamp, notes FROM experiments WHERE id=?", (experiment_id,))
            exp_res = cursor.fetchone()
            if not exp_res:
                raise DatabaseError(f"No experiment found with ID: {experiment_id}")

            data = {'id': experiment_id, 'sample_name': exp_res[0], 'timestamp': exp_res[1], 'notes': exp_res[2]}

            # Fetch raw data
            cursor.execute("SELECT angles, intensities FROM raw_data WHERE experiment_id=?", (experiment_id,))
            raw_res = cursor.fetchone()
            data['angles'] = _deserialize_array(raw_res[0])
            data['intensities'] = _deserialize_array(raw_res[1])

            # Fetch analysis results (if they exist)
            cursor.execute(
                "SELECT peaks_df_json, background_subtracted_intensities FROM analysis_results WHERE experiment_id=?",
                (experiment_id,))
            analysis_res = cursor.fetchone()
            if analysis_res:
                data['peaks_df'] = pd.read_json(analysis_res[0], orient='split')
                data['bg_sub_intensities'] = _deserialize_array(analysis_res[1])

            return data

    def get_all_experiments_summary(self):
        """Retrieves a summary of all experiments (id, name, timestamp)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, sample_name, timestamp FROM experiments ORDER BY timestamp DESC")
            return cursor.fetchall()

    def delete_experiment(self, experiment_id):
        """Deletes an experiment and all its associated data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # The database should be set up with cascading deletes, but doing it manually is safer.
                cursor.execute("DELETE FROM analysis_results WHERE experiment_id=?", (experiment_id,))
                cursor.execute("DELETE FROM raw_data WHERE experiment_id=?", (experiment_id,))
                cursor.execute("DELETE FROM experiments WHERE id=?", (experiment_id,))
                conn.commit()
                return cursor.rowcount > 0  # Returns True if a row was deleted
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Failed to delete experiment: {e}")


# =============================================================================
# Standalone Test Block
# =============================================================================

if __name__ == '__main__':
    print("--- Testing database.py ---")
    DB_FILE = "test_database.db"

    # Use a file-based DB for this test to ensure it works on disk
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    db = DatabaseManager(DB_FILE)

    # --- 1. Add an experiment ---
    print("\n[Test 1] Add new experiment...")
    try:
        angles_orig = np.linspace(10, 90, 2000)
        intensities_orig = 100 + np.random.rand(2000) * 1000
        exp_id = db.add_experiment("NaCl_Sample_1", angles_orig, intensities_orig, "First test run")
        print(f"  --> SUCCESS: Added experiment with ID: {exp_id}")
    except DatabaseError as e:
        print(f"  --> FAILED: {e}")

    # --- 2. Retrieve the experiment and verify data ---
    print("\n[Test 2] Retrieve experiment and verify data integrity...")
    try:
        data = db.get_experiment_data(exp_id)
        assert data['sample_name'] == "NaCl_Sample_1"
        assert np.array_equal(data['angles'], angles_orig)
        assert np.array_equal(data['intensities'], intensities_orig)
        print("  --> SUCCESS: Data retrieved and verified.")
    except (DatabaseError, AssertionError) as e:
        print(f"  --> FAILED: {e}")

    # --- 3. Update with analysis results ---
    print("\n[Test 3] Update with analysis results...")
    try:
        peaks_df_orig = pd.DataFrame({'angle': [31.7, 45.5], 'intensity': [1000, 800]})
        bg_sub_intensities_orig = intensities_orig - 100
        db.update_analysis_results(exp_id, peaks_df_orig, bg_sub_intensities_orig)

        # Verify the update
        data = db.get_experiment_data(exp_id)
        assert 'peaks_df' in data
        assert data['peaks_df'].equals(peaks_df_orig)
        assert np.array_equal(data['bg_sub_intensities'], bg_sub_intensities_orig)
        print("  --> SUCCESS: Analysis results updated and verified.")
    except (DatabaseError, AssertionError) as e:
        print(f"  --> FAILED: {e}")

    # --- 4. Get summary list ---
    print("\n[Test 4] Get summary of all experiments...")
    try:
        summary = db.get_all_experiments_summary()
        print(f"  Summary: {summary}")
        assert len(summary) == 1
        assert summary[0][0] == exp_id
        print("  --> SUCCESS: Summary retrieved.")
    except (DatabaseError, AssertionError) as e:
        print(f"  --> FAILED: {e}")

    # --- 5. Delete the experiment ---
    print("\n[Test 5] Delete experiment...")
    try:
        was_deleted = db.delete_experiment(exp_id)
        assert was_deleted
        summary = db.get_all_experiments_summary()
        assert len(summary) == 0
        print("  --> SUCCESS: Experiment deleted.")
    except (DatabaseError, AssertionError) as e:
        print(f"  --> FAILED: {e}")

    # --- Cleanup ---
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

