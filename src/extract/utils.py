"""
Collection of utility functions for the extract module.
"""

from pathlib import Path
from typing import List


def read_all_files_in_directory(directory: Path) -> List[Path]:
    """
    Reads all files within a directory, including files in subdirectories.

    Args:
        directory: The path to the directory.

    Returns:
        A list of Path objects representing all files found.
    """
    file_paths: List[Path] = []
    for item in directory.iterdir():
        if item.is_file():
            file_paths.append(item)
        elif item.is_dir():
            file_paths.extend(read_all_files_in_directory(item))  # Recursive call
    return file_paths


def read_all_folders_in_directory(directory: Path) -> List[Path]:
    """
    Reads all folders within a directory, including folders in subdirectories.

    Args:
        directory: The path to the directory.

    Returns:
        A list of Path objects representing all folders found.
    """
    folder_paths: List[Path] = []
    for folder in directory.iterdir():
        if folder.is_dir():
            folder_paths.append(folder)
            folder_paths.extend(read_all_folders_in_directory(folder))  # Recursive call
    return folder_paths
