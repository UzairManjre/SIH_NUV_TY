
import json
import os
from typing import Dict, Any

DATA_DIR = "backend/data"

def get_report_path(location_stretch: str) -> str:
    """Generates a clean filename for the report based on the location stretch."""
    # Sanitize the location_stretch to create a valid filename
    filename = "".join(c for c in location_stretch if c.isalnum() or c in ('-', '_')).rstrip()
    return os.path.join(DATA_DIR, f"{filename}.json")

def save_analysis(location_stretch: str, report: Dict[str, Any]):
    """Saves the analysis report to a file."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    report_path = get_report_path(location_stretch)
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)

def load_previous_analysis(location_stretch: str) -> Dict[str, Any] | None:
    """Loads the most recent previous analysis for a given location."""
    report_path = get_report_path(location_stretch)
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            return json.load(f)
    return None

def calculate_progress(previous_segmentation: Dict[str, float], current_segmentation: Dict[str, float]) -> Dict[str, float]:
    """Calculates the progress between two segmentation analyses."""
    progress = {}
    all_keys = set(previous_segmentation.keys()) | set(current_segmentation.keys())

    for key in all_keys:
        prev_percent = previous_segmentation.get(key, 0)
        curr_percent = current_segmentation.get(key, 0)
        progress[f"new_{key}_percentage"] = max(0, curr_percent - prev_percent)

    return progress

