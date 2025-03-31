# -*- coding: utf-8 -*-
"""Data formatter for Grenoble.

This module provides functionality to format ORC raw data to preprocessed data.

Version: 1.0
Date: 2025-03-31
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
TREE_PATH: Path = PROJ_ROOT / Path("config/plu_tree.yaml")
tree: Dict[str, Any] = yaml.safe_load(TREE_PATH.read_text(encoding="utf-8"))

# Loading the prompts
PROMPT_PATH: Path = PROJ_ROOT / Path("config/prompts.json")
prompts: Dict[str, str] = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))


@app.command()
def main(
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
    raw_dir: Path = typer.Option(RAW_DATA_DIR, "--output-dir", "-r"),
    int_dir: str = typer.Option(INTERIM_DATA_DIR, "--int-dir", "-i"),
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
    data: dict = formatter.prepare_data()

    for key, value in data.items():
        assert value, f"Data for {key} is empty: {value}"

    # Save the formatted data as JSON
    output_path: Path = int_dir / Path(f"data_{folder.lower()}.json")
    output_path.parent.mkdir(exist_ok=True, parents=True)

    save_as_json(data, output_path)
    logger.success(f"Formatted data saved to {output_path}")


if __name__ == "__main__":
    app()
