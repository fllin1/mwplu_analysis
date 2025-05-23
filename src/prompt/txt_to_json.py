# -*- coding: utf-8 -*-
"""Text file to JSON converter for prompts.

Simply run this file to convert text format prompt located in the `/references/` folder
to JSON format in the `/config/` folder.

Version: 1.1
Date: 2025-05-20
Author: Grey Panda
"""

from pathlib import Path

import json
from loguru import logger
from src.config import CONFIG_DIR, REFERENCES_DIR


def convert_prompts_txt_to_json():
    """
    Convert text files to JSON format.
    This function reads the text files located in the `/references/` folder,
    converts them to JSON format, and saves them in the `/config/` folder.
    """
    # Define the paths to the text files
    path_prompt_plu: Path = REFERENCES_DIR / "prompt" / "prompt_plu.txt"
    path_prompt_oap: Path = REFERENCES_DIR / "prompt" / "prompt_oap.txt"
    path_prompt_reglement_zone: Path = (
        REFERENCES_DIR / "prompt" / "references/prompt_reglement_zone.txt"
    )

    # Read the text files and convert them to JSON format
    prompt_oap: str = path_prompt_oap.read_text(encoding="utf-8")
    prompt_plu: str = path_prompt_plu.read_text(encoding="utf-8")
    prompt_reglement_zone: str = path_prompt_reglement_zone.read_text(encoding="utf-8")

    prompt_json = {
        "prompt_plu": prompt_plu,
        "prompt_oap": prompt_oap,
        "prompt_reglement_zone": prompt_reglement_zone,
    }

    # Save the JSON data to a file
    save_path: Path = CONFIG_DIR / "prompt" / "prompt.json"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(
        json.dumps(prompt_json, indent=4, ensure_ascii=False), encoding="utf-8"
    )
    logger.success(f"Prompts saved to {save_path}")


if __name__ == "__main__":
    convert_prompts_txt_to_json()
