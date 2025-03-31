# -*- coding: utf-8 -*-
"""Data analysis module.

This module provides functionality to analyse preprocessed data with the Google GenAI API.

Version: 1.0
Date: 2025-03-31
Author: Florent Lin
"""

import json
from pathlib import Path
from typing import Any, Dict

import typer
import yaml
from google.genai import types
from google.genai.errors import ClientError
from loguru import logger
from PIL import Image

from src.api.gemini_thinking import gemini_api
from src.config import INTERIM_DATA_DIR, PROCESSED_DATA_DIR, PROJ_ROOT
from src.prompt.prompt_config import CONFIG_TEMPLATE
from src.static.prompt_format import format_all_prompt_plu
from src.utils import save_as_json

app = typer.Typer(pretty_exceptions_enable=False)

# Loading the tree data structure
TREE_PATH: Path = PROJ_ROOT / Path("config/plu_tree.yaml")
tree: Dict[str, Any] = yaml.safe_load(TREE_PATH.read_text(encoding="utf-8"))

# Loading the prompts
PROMPT_PATH: Path = PROJ_ROOT / Path("config/prompts.json")
prompts: Dict[str, str] = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))


@app.command()
def main(
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
    int_dir: Path = typer.Option(INTERIM_DATA_DIR, "--int-dir", "-i"),
    proc_dir: Path = typer.Option(PROCESSED_DATA_DIR, "--output-dir", "-o"),
    model_name: str = typer.Option(
        "gemini-2.5-pro-exp-03-25", "--model-name", "-m", help="Model name"
    ),
) -> list:
    """
    Main function to format the data for the city of Grenoble.
    Returns a list of zones that were skipped due to token limit errors.
    """
    # All the zones that were skipped due to token limit errors
    skipped_zones = []

    # Loop through all PLU
    path_preprocessed_data: Path = int_dir / Path(f"data_{folder.lower()}.json")
    preprocessed_data = json.loads(path_preprocessed_data.read_text(encoding="utf-8"))

    prompts_plu = format_all_prompt_plu(
        tree=tree, prompt=prompts, folder=folder, preprocessed_data=preprocessed_data
    )

    # API Call loop
    for zone_type_name, zone_data in prompts_plu.items():
        logger.info(f"Processing zone type: {zone_type_name}")

        for zone_name, parts in zone_data.items():
            assert isinstance(parts, list), (
                f"{zone_name} is not of type list: {type(parts)}"
            )
            for part in parts:
                assert isinstance(part, (types.Part, Image.Image)), (
                    f"{zone_name} is not of type types.Part or Image.Image: {type(part)}"
                )

            output_dir = proc_dir / Path(folder) / Path(zone_type_name)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = (output_dir / Path(zone_name)).with_suffix(".json")

            try:
                response = gemini_api(
                    model_name=model_name,
                    contents=parts,
                    generate_content_config=CONFIG_TEMPLATE,
                )
                save_as_json(
                    data=response.to_json_dict(),
                    path=output_file,
                )
                logger.success(f"File saved: {output_file}")

            except ClientError as e:
                error_message = str(e)
                # Si erreur de limite de tokens, on saute cette zone
                if (
                    "The input token count" in error_message
                    and "exceeds the maximum number of tokens allowed" in error_message
                ):
                    logger.warning(f"{zone_name} skipped due to : {error_message}")
                    logger.info(f"Number of parts : {len(parts)}")
                    skipped_zones.append(zone_name)
                else:
                    raise

    logger.info(f"Processing completed {skipped_zones} skipped.")


if __name__ == "__main__":
    skipped = app()
    if skipped:
        print(f"Zones sautées en raison de limite de tokens: {skipped}")
