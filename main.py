#!/usr/bin/env python3
"""
Main orchestrator for the CPC (Cooperative Patent Classification) analysis pipeline.
This script performs the following steps:
1. Parses raw CPC text files to create a hierarchical JSON and a flat TSV.
2. Runs supplementary analysis scripts on the generated outputs.
"""
import os
import subprocess

# --- Configuration ---
# Use os.path for compatibility with older Python versions
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define key directory paths using os.path.join
DATA_DIR = os.path.join(BASE_DIR, "data", "cpc_title_lists")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
SUPPLEMENTARY_DIR = os.path.join(SCRIPTS_DIR, "supplementary")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# --- Main Pipeline ---

def run_script(script_path):
    """Executes a Python script and checks for errors."""
    script_name = os.path.basename(script_path)
    print("\n" + "="*20)
    print("Running: {}".format(script_name))
    print("="*20)
    try:
        result = subprocess.run(
            ['python3', script_path], 
            check=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8' # Explicitly set encoding
        )
        print(result.stdout)
        if result.stderr:
            print("--- Stderr ---")
            print(result.stderr)
        print("--- Finished {} ---".format(script_name))
    except subprocess.CalledProcessError as e:
        print("!!! ERROR running {} !!!".format(script_name))
        print("Return Code: {}".format(e.returncode))
        print("\n--- STDOUT ---")
        print(e.stdout)
        print("\n--- STDERR ---")
        print(e.stderr)
        # Exit the main script if a crucial step fails
        if script_name in ["cpc_parser.py"]:
             exit(1)
    except Exception as e:
        print("An unexpected error occurred while running {}: {}".format(script_name, e))
        exit(1)


def main():
    """Run the full CPC analysis pipeline."""
    print("Starting CPC Data Processing and Analysis Pipeline...")
    
    # Ensure output directories exist
    os.makedirs(os.path.join(OUTPUT_DIR, "breadth_analysis"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "depth_analysis"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "taxonomy"), exist_ok=True)

    # Step 1: Parse the raw CPC files into JSON and TSV formats
    run_script(os.path.join(SCRIPTS_DIR, "cpc_parser.py"))

    # Step 2: Run supplementary analysis and visualization scripts
    print("\n--- Running Supplementary Analyses ---")
    
    supplementary_scripts = [
        "analyze_cluster_breadth.py",
        "analyze_hierarchy_permutations.py",
        "prepare_for_echarts.py",
        "sample_hierarchy.py"
    ]

    for script in supplementary_scripts:
        run_script(os.path.join(SUPPLEMENTARY_DIR, script))
        
    print("\n\nPipeline finished successfully!")
    print("All outputs are located in: {}".format(OUTPUT_DIR))
    print("To view the interactive tree, open this file in your browser: {}".format(os.path.join(SUPPLEMENTARY_DIR, 'visualize_cpc.html')))


if __name__ == "__main__":
    main()