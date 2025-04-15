# -*- coding: utf-8 -*-
"""Data formatter for Grenoble.

This module provides functionality to format ORC raw data to preprocessed data.

Version: 1.1
Date: 2025-04-05
Author: Grey Panda
"""

import json
from pathlib import Path
from typing import Any, Dict

import typer
import yaml
from loguru import logger

from src.config import INTERIM_DATA_DIR, PROJ_ROOT, RAW_DATA_DIR
from src.static.preprocess import Preprocess
from src.utils import save_as_json

app = typer.Typer(pretty_exceptions_enable=False)

# Loading file organisation data
# NOTE: This variable is used only to get the documents_par_zone names
TREE_PATH: Path = PROJ_ROOT / Path("config/plu_tree.yaml")
tree: Dict[str, Any] = yaml.safe_load(TREE_PATH.read_text(encoding="utf-8"))

# Loading the prompts
PROMPT_PATH: Path = PROJ_ROOT / Path("config/prompts.json")
prompts: Dict[str, str] = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))


@app.command()
def main(
    folder: str = typer.Option("grenoble", "--folder", "-f", help="City folder"),
    raw_dir: Path = typer.Option(RAW_DATA_DIR, "--output-dir", "-r"),
    int_dir: Path = typer.Option(INTERIM_DATA_DIR, "--int-dir", "-i"),
    model_name: str = typer.Option(
        "gemini-2.5-pro-exp-03-25",
        "--model-name",
        "-m",
        help="Model name to use for the page extraction",
    ),
) -> None:
    formatter = Preprocess(
        folder=folder,
        raw_dir=raw_dir,
        model_name=model_name,
        tree=tree,
        prompts=prompts,
    )
    documents_pages: list = formatter.get_pages()

    output_path: Path = int_dir / Path(folder).with_suffix(".json")
    if output_path.exists():
        results = json.loads(output_path.read_text(encoding="utf-8"))
        logger.info(f"Loaded existing data from {output_path}")
    else:
        results = {}

    for zone, document_pages in documents_pages.items():
        assert isinstance(document_pages, list), (
            f"{document_pages} not a list: {type(document_pages)}"
        )

        results[zone] = document_pages

    # Save the formatted data as JSON
    save_as_json(results, output_path)
    logger.success(f"Formatted data saved to {output_path}")


if __name__ == "__main__":
    app()
