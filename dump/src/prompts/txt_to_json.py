# -*- coding: utf-8 -*-
"""Text file to JSON converter for prompts.

Simply run this file to convert text format prompt located in the `/references/` folder
to JSON format in the `/config/` folder.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

from pathlib import Path

import json
from loguru import logger
from src.config import PROJ_ROOT

# Define the paths to the text files
path_prompt_plu: Path = PROJ_ROOT / Path("references/prompt_plu.txt")
path_prompt_oap: Path = PROJ_ROOT / Path("references/prompt_oap.txt")
path_prompt_reglement_zone: Path = PROJ_ROOT / Path(
    "references/prompt_extract_zones.txt"
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
save_path: Path = PROJ_ROOT / Path("config/prompts.json")
save_path.parent.mkdir(parents=True, exist_ok=True)
save_path.write_text(
    json.dumps(prompt_json, indent=4, ensure_ascii=False), encoding="utf-8"
)
logger.success(f"Prompts saved to {save_path}")
