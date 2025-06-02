#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate PLU Configuration Files
This script scans the data directories and generates YAML configuration files
for external, raw, interim, and processed PLU data.

For processed data, it includes source_plu_url fields and preserves existing values
when re-running the script.

Version: 1.0
Date: 2025-05-28
Author: Grey Panda
"""

from pathlib import Path
from typing import Any, Dict

import yaml
from loguru import logger


def scan_directory(directory: Path) -> Dict[str, Any]:
    """
    Recursively scan a directory and return its structure.

    Args:
        directory: Path to the directory to scan

    Returns:
        Dictionary representing the directory structure
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return {}

    structure = {}
    base_path = Path.cwd()

    try:
        for item in sorted(directory.iterdir()):
            if item.is_file() and not item.name.startswith("."):
                # For files, store basic info
                try:
                    relative_path = item.relative_to(base_path)
                except ValueError:
                    # If relative_to fails, use the absolute path
                    relative_path = item.resolve()

                structure[item.name] = {
                    "type": "file",
                    "path": str(relative_path),
                    "size_bytes": item.stat().st_size,
                }
            elif item.is_dir() and not item.name.startswith("."):
                # For directories, recursively scan
                try:
                    relative_path = item.relative_to(base_path)
                except ValueError:
                    # If relative_to fails, use the absolute path
                    relative_path = item.resolve()

                structure[item.name] = {
                    "type": "directory",
                    "path": str(relative_path),
                    "contents": scan_directory(item),
                }
    except PermissionError as e:
        logger.error(f"Permission error scanning {directory}: {e}")

    return structure


def load_existing_yaml(yaml_path: Path) -> Dict[str, Any]:
    """
    Load existing YAML file if it exists.

    Args:
        yaml_path: Path to the YAML file

    Returns:
        Dictionary with existing data or empty dict
    """
    if yaml_path.exists():
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading existing YAML {yaml_path}: {e}")
            return {}
    return {}


def preserve_source_plu_urls(
    new_structure: Dict[str, Any], existing_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Preserve existing source_plu_url values from the existing data.

    Args:
        new_structure: Newly scanned directory structure
        existing_data: Existing YAML data

    Returns:
        Updated structure with preserved source_plu_url values
    """

    def merge_recursive(
        new_dict: Dict[str, Any], existing_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        for key, value in new_dict.items():
            if key in existing_dict:
                if isinstance(value, dict) and isinstance(existing_dict[key], dict):
                    # If both are dicts, merge recursively
                    if "source_plu_url" in existing_dict[key]:
                        # Preserve the source_plu_url if it exists
                        value["source_plu_url"] = existing_dict[key]["source_plu_url"]
                    if "contents" in value and "contents" in existing_dict[key]:
                        value["contents"] = merge_recursive(
                            value["contents"], existing_dict[key]["contents"]
                        )
                    elif "contents" in existing_dict[key]:
                        # Preserve other fields that might exist
                        for existing_key, existing_value in existing_dict[key].items():
                            if existing_key not in value:
                                value[existing_key] = existing_value
        return new_dict

    return merge_recursive(new_structure, existing_data)


def add_source_plu_url_fields(
    structure: Dict[str, Any], level: int = 0
) -> Dict[str, Any]:
    """
    Add source_plu_url fields to city-level entries in processed data.

    Args:
        structure: Directory structure dictionary
        level: Current nesting level (0=root, 1=city, 2=zoning, etc.)

    Returns:
        Updated structure with source_plu_url fields
    """
    updated_structure = structure.copy()

    for key, value in updated_structure.items():
        if isinstance(value, dict):
            if level == 0 and value.get("type") == "directory":
                # This is a city directory, add source_plu_url if not exists
                if "source_plu_url" not in value:
                    value["source_plu_url"] = None

            # Recursively process contents
            if "contents" in value:
                value["contents"] = add_source_plu_url_fields(
                    value["contents"], level + 1
                )

    return updated_structure


def save_yaml_config(data: Dict[str, Any], output_path: Path, description: str):
    """
    Save data to a YAML file with metadata.

    Args:
        data: Data to save
        output_path: Path to save the file
        description: Description for the file header
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare the complete structure with metadata
    yaml_content = {
        "metadata": {
            "description": description,
            "generated_at": str(Path.cwd()),
            "total_items": len(data),
        },
        "data": data,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                yaml_content,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        logger.success(f"Generated {output_path}")
    except Exception as e:
        logger.error(f"Error saving YAML to {output_path}: {e}")


def main():
    """Main function to generate all PLU configuration files."""

    # Define paths
    base_data_dir = Path("data")
    config_dir = Path("config/plu")

    directories_to_scan = {
        "external": {
            "path": base_data_dir / "external",
            "output": config_dir / "plu_external.yaml",
            "description": "External PLU data files and resources",
        },
        "raw": {
            "path": base_data_dir / "raw",
            "output": config_dir / "plu_raw.yaml",
            "description": "Raw PLU data files before processing",
        },
        "interim": {
            "path": base_data_dir / "interim",
            "output": config_dir / "plu_interim.yaml",
            "description": "Intermediate PLU data during processing",
        },
        "processed": {
            "path": base_data_dir / "processed",
            "output": config_dir / "plu_processed.yaml",
            "description": "Processed PLU data ready for analysis",
        },
    }

    for data_type, config in directories_to_scan.items():
        logger.info(f"Scanning {data_type} directory: {config['path']}")

        # Scan the directory structure
        structure = scan_directory(config["path"])

        if data_type == "processed":
            # Special handling for processed data
            # Load existing data to preserve source_plu_url values
            existing_data = load_existing_yaml(config["output"])
            existing_structure = existing_data.get("data", {})

            # Add source_plu_url fields for cities
            structure = add_source_plu_url_fields(structure)

            # Preserve existing source_plu_url values
            structure = preserve_source_plu_urls(structure, existing_structure)

        # Save to YAML file
        save_yaml_config(structure, config["output"], config["description"])

    logger.success("PLU configuration generation completed!")


if __name__ == "__main__":
    main()
