# -*- coding: utf-8 -*-
"""Data saving utilities.

This module provides utility functions for saving data.

Version: 1.1
Date: 2025-04-04
Author: Grey Panda
"""

import json
from pathlib import Path


def save_as_json(data: dict, save_path: Path) -> None:
    """
    Saves the OCR response as a JSON file.

    Args:
        data: (dict) The data to save.
        save_path: (Path) The path to save the JSON file.
    """
    save_path.parent.mkdir(exist_ok=True, parents=True)
    save_path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8"
    )


def remove_text_outside_json(text: str) -> str:
    """
    Removes text outside the first and last bracket in a string.
    Args:
        texte: (str) The input string.
    Returns:
        str: The modified string with text outside the first and last bracket removed.
    """
    first_bracket = text.find("{")
    last_bracket = text.rfind("}")

    if first_bracket == -1 or last_bracket == -1:
        return text  # If no brackets are found, return the original text

    if last_bracket < first_bracket:
        return text  # Case where the last bracket is before the first one

    return text[first_bracket : last_bracket + 1]
