# -*- coding: utf-8 -*-
"""
Lille Zones Spécifiques
This module processes JSON files in the data/processed/lille directory to identify and move files
with 'name_plu': 'zones_specifiques' to the correct folder structure.
"""

import json
from pathlib import Path


def process_zones_specifiques():
    """
    Process JSON files in data/processed/lille directory to identify and move files with
    'name_plu': 'zones_specifiques' to the correct folder structure.
    """
    # Source directory where JSON files are currently located
    source_dir = Path("data/processed/lille")

    # Target directory for zones specifiques
    target_dir = Path("data/processed/lille/Zones Spécifiques")

    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)

    # Counter for processed files
    processed_count = 0

    # Walk through all files in the source directory and subdirectories
    for json_file in source_dir.rglob("*.json"):
        try:
            # Read the JSON file
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if this file has zones_specifiques in metadata
            metadata = data.get("metadata", {})
            if metadata.get("name_plu") == "zones_specifiques":
                print(f"Processing: {json_file}")

                # Update the name_zoning in metadata
                metadata["name_zoning"] = "Zones Spécifiques"

                # Create the target file path
                target_file = target_dir / json_file.name

                # Write the updated JSON to the target location
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

                # Remove the original file
                json_file.unlink()

                print(f"  -> Moved to: {target_file}")
                processed_count += 1

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error processing {json_file}: {e}")
            continue

    print(f"\nProcessed {processed_count} files with 'zones_specifiques'")


if __name__ == "__main__":
    process_zones_specifiques()
