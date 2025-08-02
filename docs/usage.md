# oneXRD User Manual & Tutorial

## 1. Introduction

Welcome to **oneXRD**!

**oneXRD** is a powerful, user-friendly, and extensible software for powder X-ray diffraction (XRD) analysis. It is designed to provide researchers with an intuitive and efficient tool to visualize, process, analyze, and manage their XRD data without the high cost of commercial software.

This guide will walk you through the main features of the application and provide a step-by-step tutorial for a typical analysis workflow.

## 2. The Main Interface

The **oneXRD** interface is designed to be clean and intuitive. It is composed of four main sections:

![oneXRD Main Interface](3563f97f7328056d3ca7d5228816771c.png)

1.  **The Plot Panel (Top Right):** This is the main canvas where your XRD patterns are displayed. It includes a built-in toolbar at the bottom that allows you to:
    *   **Pan** across the data.
    *   **Zoom** into regions of interest.
    *   **Configure** subplots.
    *   **Save** the current plot as a high-quality image for publications or presentations.

2.  **The Control Panel (Left):** This panel contains all the interactive tools for your analysis.
    *   **Background Subtraction:** Tools to remove the amorphous background signal from your data.
    *   **Peak Finding:** Controls to automatically identify diffraction peaks after background subtraction.
    *   **Project Database:** A list of all your saved experiments. From here, you can **Save** your current work, **Load** a past experiment, or **Delete** an entry.

3.  **The Results Panel (Bottom Right):**
    *   **Identified Peaks:** Once you perform a peak search, this table will populate with a detailed list of every peak found, including its precise angle, intensity, prominence, and Full-Width at Half-Maximum (FWHM).

4.  **The Status Bar (Bottom Left):** This bar provides helpful feedback on the current state of the application, such as when a file is loading or when an analysis is complete.

## 3. Basic Workflow: A Step-by-Step Tutorial

This tutorial will guide you through the most common workflow, from loading a raw data file to finding its peaks.

### Step 1: Load Your Data

Begin by loading an experimental data file.
*   Go to `File > Open File...` in the top menubar.
*   Select your data file. **oneXRD** supports most common formats, including Bruker (`.raw`), PANalytical (`.xrdml`), and generic two-column text files (`.xy`, `.csv`, `.txt`).

Your data will appear in the Plot Panel.

### Step 2: Subtract the Background

Raw XRD data typically includes a broad, curved background that needs to be removed.

1.  In the **Background Subtraction** section, select a method. The `Iterative Erosion` method is a great, automated starting point.
2.  Enter a value in the `Iterations` box. This controls how aggressively the background is removed. A good starting value is between **50** and **100**. A higher number will create a smoother, flatter background.
3.  Click the **Apply Background** button.

You will see two things happen: the main plot will update to show the background-subtracted data (the peaks should now start near zero intensity), and a red dashed line will appear showing the background that was calculated and removed. To undo this step at any time, simply click **Clear Background**.

### Step 3: Find the Peaks

With the background removed, you can now automatically identify the peaks.

1.  In the **Peak Finding** section, you can set filters to avoid detecting noise.
    *   `Min Height`: Sets a minimum absolute intensity for a peak to be considered.
    *   `Min Prominence`: A powerful filter that measures how much a peak "stands out" from the surrounding data. It is often more effective than height for noisy patterns. Start with a small value (e.g., 50) and increase it if too many noise peaks are being identified.
2.  Click the **Find Peaks** button.

The plot will update to show black 'x' markers on every peak that was found, and the **Identified Peaks** table will populate with detailed information for each one.

### Step 4: Save Your Work

To save your experiment for later, you can add it to the project database.

1.  In the **Project Database** panel, click the **Save** button.
2.  A dialog box will appear asking for a sample name. Enter a descriptive name and click OK.
3.  Your experiment will now appear in the Project Database list, and its raw data and analysis steps are saved permanently.

To reload this experiment in the future, simply select it from the list and click **Load**.

## 4. Advanced Usage: Phase Identification

Once you have identified the peaks in an unknown sample, you can compare them to a known reference material from a `.cif` (Crystallographic Information File).

1.  First, load and process your experimental data as described in the tutorial above.
2.  Next, go to `File > Open File...` again, but this time select a `.cif` file for a reference compound (e.g., `NaCl.cif`).
3.  The reference pattern will be overlaid on your experimental data as a series of green vertical lines, allowing for a direct visual comparison. The `Search-Match` analysis module will use this data to calculate a "Figure of Merit" score, quantifying how well the patterns match.

## 5. Extending Functionality with Plugins

**oneXRD** is designed to be extensible. Advanced functions, such as Rietveld refinement, quantitative analysis, or batch processing, can be added via plugins.

**To install a plugin:**
1.  Locate the `plugins` directory next to the main `oneXRD` application folder.
2.  Place the new plugin's folder inside this `plugins` directory.
3.  Restart **oneXRD**.

The new functionality provided by the plugin will automatically appear in the application, typically in a new menu in the top menubar.