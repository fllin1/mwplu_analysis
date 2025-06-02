# -*- coding: utf-8 -*-
"""
This module contains functions to normalize paths and filenames.
"""
import unicodedata
import re
from pathlib import Path


def normalize_filename(filename: str) -> str:
    """
    Normalize a filename by handling special characters.

    Args:
        filename (str): The original filename

    Returns:
        str: The normalized filename (lowercase, no accents,
        special characters replaced by underscores)
    """
    normalized = filename.lower()

    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )

    special_chars = [
        " ",
        "'",
        '"',
        "-",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "&",
        "+",
        "=",
        "@",
        "#",
        "%",
        "!",
        "?",
        ",",
        ";",
        ":",
    ]
    for char in special_chars:
        normalized = normalized.replace(char, "_")

    normalized = re.sub(r"[^a-z0-9._]", "_", normalized)

    normalized = re.sub(r"_+", "_", normalized)

    normalized = normalized.strip("_")

    if "." in normalized:
        name_part, ext_part = normalized.rsplit(".", 1)
        name_part = name_part.strip("_")
        normalized = f"{name_part}.{ext_part}"

    return normalized


def normalize_path(file_path: str) -> str:
    """
    Normalize a complete path by applying normalization to each part of the path.

    Args:
        file_path (str): The original complete path

    Returns:
        str: The normalized path
    """
    path = Path(file_path)

    normalized_parts = []
    for part in path.parts:
        if part == "/" or part.endswith(":"):
            normalized_parts.append(part)
        else:
            normalized_parts.append(normalize_filename(part))

    return str(Path(*normalized_parts))
