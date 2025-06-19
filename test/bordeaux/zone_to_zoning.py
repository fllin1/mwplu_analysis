# -*- coding: utf-8 -*-
"""
This script is used to process the zone files for the Bordeaux region.
It is used to create the new zone files for the Bordeaux region.
"""

import json
import os

from src.config import INTERIM_DATA_DIR

ZONE_MAPPING = {
    "Zones Agricoles": ["Zones A"],
    "Zones Naturelles": ["Zones N"],
    "Zones à Urbaniser": ["Zones AU"],
    "Zones Urbaines": ["Zones UM", "Zones US", "Zones UPZ", "Zones UP"],
}

BASE_DIR = INTERIM_DATA_DIR / "bordeaux"


def process_zone_files():
    """
    Process the zone files for the Bordeaux region.
    It is used to create the new zone files for the Bordeaux region.
    """
    for new_zone_name, old_zone_dirs in ZONE_MAPPING.items():
        new_zone_path = BASE_DIR / new_zone_name
        new_zone_path.mkdir(parents=True, exist_ok=True)

        print(f"Processing for new zone: {new_zone_name}")

        for old_zone_dir_name in old_zone_dirs:
            old_zone_path = BASE_DIR / old_zone_dir_name

            if not old_zone_path.exists():
                print(f"Warning: Old zone directory not found: {old_zone_path}")
                continue

            for json_file in old_zone_path.glob("*.json"):
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Modify the name_zoning field
                data["metadata"]["name_zoning"] = new_zone_name

                # Define the new file path
                destination_file_path = new_zone_path / json_file.name

                # Save the modified JSON to the new directory
                with open(destination_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            # Optionally, remove the original file after copying and modification
            os.remove(old_zone_path)


if __name__ == "__main__":
    process_zone_files()
