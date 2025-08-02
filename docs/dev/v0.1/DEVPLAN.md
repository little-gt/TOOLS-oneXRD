Detailed directory structure for **oneXRD**.

```
PROJECT/
├── docs/
│   ├── api/                  # For auto-generated API documentation
│   └── usage.md              # User manual and tutorials
│
├── plugins/                  # <-- User-facing: for installing advanced plug-ins
│   ├── batch_processing/
│   │   ├── __init__.py       # Plug-in registration file
│   │   └── ui.py             # UI for setting up batch jobs
│   │
│   ├── microstructure_analysis/
│   │   ├── __init__.py       # Plug-in registration file
│   │   ├── analysis.py       # Williamson-Hall, Scherrer calculations
│   │   └── ui.py             # UI for microstructure analysis
│   │
│   ├── quantitative_analysis/
│   │   ├── __init__.py       # Plug-in registration file
│   │   ├── analysis.py       # RIR and other quantitative methods
│   │   └── ui.py             # UI for quantitative analysis
│   │
│   └── rietveld_refinement/
│       ├── __init__.py       # Plug-in registration file
│       ├── engine.py         # The core refinement logic (or wrapper for GSAS-II)
│       └── ui.py             # Advanced UI for controlling refinement
│
├── oneXRD/                   # <-- Main source code package
│   ├── __main__.py           # Entry point: python -m oneXRD
│   │
│   ├── main_app.py           # The main Application class, ties everything together
│   │
│   ├── analysis/             # Core scientific analysis algorithms
│   │   ├── __init__.py
│   │   ├── background.py     # Background subtraction functions
│   │   ├── fitting.py        # Peak profile fitting (Gaussian, etc.)
│   │   ├── peak_finding.py   # Peak detection algorithms
│   │   └── search_match.py   # Logic for comparing exp. peaks to reference
│   │
│   ├── core/                 # Fundamental data objects and database logic
│   │   ├── __init__.py
│   │   ├── database.py       # Handles all SQLite database interactions
│   │   ├── project.py        # Defines the "Project" class that holds all session data
│   │   └── xrd_data.py       # The XRDData class that holds intensities, angles, etc.
│   │
│   ├── importers/            # Universal importer system for all file formats
│   │   ├── __init__.py       # The main `load_data(filepath)` engine
│   │   └── readers/          # Individual modules for each file format
│   │       ├── __init__.py
│   │       ├── bruker_reader.py
│   │       ├── cif_reader.py
│   │       ├── generic_reader.py # For .xy, .csv
│   │       └── panalytical_reader.py
│   │
│   ├── plugins_api/          # The internal system for managing plug-ins
│   │   ├── __init__.py
│   │   ├── api.py            # Defines the stable API passed to plug-ins
│   │   └── manager.py        # Discovers, loads, and manages all plug-ins
│   │
│   └── ui/                   # All UI components (using customtkinter)
│       ├── __init__.py
│       ├── assets/           # Icons, themes, etc.
│       ├── frames/           # Modular UI frames
│       │   ├── __init__.py
│       │   ├── analysis_frame.py
│       │   ├── database_frame.py
│       │   ├── peak_list_frame.py
│       │   └── plot_frame.py
│       └── main_window.py    # The main window that assembles all the frames
│
├── tests/                    # Unit and integration tests for all modules
│   ├── test_analysis.py
│   ├── test_database.py
│   └── test_importers.py
│
├── pyproject.toml            # Modern Python project definition, dependencies
├── README.md                 # Project description and setup instructions
└── .gitignore                # To exclude temporary files from version control
```

### Structure Maps to Phased Development

This structure is designed to be built in the exact order we discussed, ensuring a logical and manageable workflow.

*   **Phase 1: Core Data Visualization**
    *   **Focus:** We will build the skeletons of `oneXRD/ui/main_window.py` and `oneXRD/ui/frames/plot_frame.py`.
    *   **Focus:** We will implement the first simple reader in `oneXRD/importers/readers/generic_reader.py` and the basic engine in `oneXRD/importers/__init__.py`.
    *   **Result:** A runnable application that can open a `.xy` file and plot it.

*   **Phase 2: Foundational Analysis Tools**
    *   **Focus:** We will build the functions within `oneXRD/analysis/background.py` and `oneXRD/analysis/peak_finding.py`.
    *   **Focus:** We will build the UI for these tools in `oneXRD/ui/frames/analysis_frame.py` and `oneXRD/ui/frames/peak_list_frame.py`.
    *   **Result:** The application becomes a useful tool for basic data processing.

*   **Phase 3: Database and Intelligence**
    *   **Focus:** We will build the entire `oneXRD/core/` module to handle project state and SQLite storage.
    *   **Focus:** We will implement `oneXRD/analysis/search_match.py` and the UI in `oneXRD/ui/frames/database_frame.py` to connect to the COD.
    *   **Result:** The application is now a complete, standalone analysis program for the most common research tasks.

*   **Phase 4: Extensibility and Advanced Functions**
    *   **Focus:** We will build the entire `oneXRD/plugins_api/` system. This is a critical step that makes everything else possible.
    *   **Focus:** With the API complete, we can begin developing the advanced plug-ins one by one and placing them in the top-level `plugins/` directory. Each plug-in (e.g., `quantitative_analysis/`, `rietveld_refinement/`) is a self-contained project that uses the stable API, ensuring the core application remains untouched and stable.