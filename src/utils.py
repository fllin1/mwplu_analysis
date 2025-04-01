# -*- coding: utf-8 -*-
"""Data saving utilities.

This module provides utility functions for saving data.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

import json
from pathlib import Path


def save_as_json(data: dict, save_path: Path) -> None:
    """
    Sauvegarde la réponse OCR au format JSON.

    Args:
        ocr_response: (dict) La réponse OCR à sauvegarder.
        save_path: (str) Le chemin où sauvegarder le fichier JSON.
    """
    save_path.parent.mkdir(exist_ok=True, parents=True)
    save_path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8"
    )
