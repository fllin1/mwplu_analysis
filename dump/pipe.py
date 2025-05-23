# -*- coding: utf-8 -*-
"""
PLU Pipeline.

This script allows running OCR or synthesis tasks in batch mode based on a configuration file.

It reads the configuration from `config/pipeline_config.json` and presents a menu
to the user to choose between running all OCR tasks or all synthesis tasks defined
in the configuration.

Usage:
    1. Ensure `config/pipeline_config.json` is correctly configured with the desired PLUs and zones.
       Example structure:
       {
         "cities": [
           {
             "name": "grenoble",
             "plus": [
               {"plu": "plu_grenoble_1"},
               {"plu": "plu_grenoble_2"}
             ],
             "zones": [
               {"zone": "Zone_UB_grenoble", "regles_communes": true},
               {"zone": "Zone_UC_grenoble", "file": "custom_file_name"}
             ]
           },
           {
             "name": "paris",
             "plus": [
               {"plu": "plu_paris_1"}
             ],
             "zones": [
               {"zone": "Zone_UA_paris", "regles_communes": false}
             ]
           }
         ]
       }
    2. Run the script from the command line:
       python pipe.py
    3. Select the desired batch operation (OCR or Synthesis) from the menu.

Version: 1.2
Date: 2025-04-13
Author: Grey Panda
"""

import json
import subprocess
import sys
from pathlib import Path

from loguru import logger


def run_command(cmd: str) -> None:
    """
    Executes a shell command using subprocess.run and logs the command.

    Args:
        cmd: The shell command string to execute.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit code.
    """
    logger.debug(f"Executing: {cmd}")
    subprocess.run(cmd, shell=True, check=True)  # Added check=True to raise errors


def run_batch_ocr(config: dict) -> None:
    """
    Iterates through the 'plus' list in the configuration dictionary
    and runs the OCR command (`main.py ocr`) for each PLU item.

    Args:
        config: The pipeline configuration dictionary loaded from JSON.
    """
    folder = config.get("name")
    for plu_item in config.get("plus", []):
        plu = plu_item["plu"]

        cmd = f"python main.py ocr {plu} --folder {folder}"
        run_command(cmd)


def run_batch_synthesis(config: dict) -> None:
    """
    Iterates through the 'zones' list in the configuration dictionary
    and runs the synthesis command (`main.py synthesis`) for each zone item.

    Args:
        config: The pipeline configuration dictionary loaded from JSON.
    """
    city = config.get("name")
    for zone_item in config.get("zones", []):
        zone = zone_item["zone"]

        # Build the command
        cmd = f"python main.py synthesis {zone} --city {city}"

        # Add the regles-communes parameter if specified and false
        if "regles_communes" in zone_item and not zone_item["regles_communes"]:
            cmd += " --regles-communes"

        # Add the file parameter if specified
        if "file" in zone_item:
            cmd += f" --file {zone_item['file']}"

        run_command(cmd)


if __name__ == "__main__":
    config_file = Path("config/pipeline_config.json")
    assert config_file.exists(), logger.error(f"{config_file} does not exist.")

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("\n1. Run all OCR tasks")
    print("2. Run all synthesis tasks")
    print("3. Exit")

    choice = input("\nYour choice (1-3): ")

    for city_config in config["cities"]:  # Use config instead of config_file
        city_name = city_config["name"]
        logger.info(f"Processing city: {city_name}")

        if choice == "1":
            run_batch_ocr(city_config)
        elif choice == "2":
            run_batch_synthesis(city_config)
        elif choice == "3":
            logger.info("Exiting.")
            sys.exit(0)
        else:
            logger.error("Invalid choice.")
            break
