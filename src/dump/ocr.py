# -*- coding: utf-8 -*-
"""PDF OCR processor using Mistral.

This module extracts text from PDF files using Mistral OCR with base64 images,
converting the content to JSON format.

Version: 1.1
Date: 2025-04-04
Author: Grey Panda
"""

from pathlib import Path
from typing import Any, Dict, List

import typer
import yaml
from loguru import logger
from tqdm import tqdm

from src.config import (
    EXTERNAL_DATA_DIR,
    PROJ_ROOT,
    RAW_DATA_DIR,
)
from src.api.mistral_ocr import (
    mistral_ocr,
    push_to_mistral,
)
from src.utils import save_as_json

# Create Typer app
app = typer.Typer()

# Loading file organisation data
with open(PROJ_ROOT / "config/plu_tree.yaml", "r", encoding="utf-8") as f:
    TREE = yaml.safe_load(f)


def _append_paths_dict(paths: list, file_name: str, ext_dir: Path, raw_dir: Path):
    """
    Appends the input and output paths to the list of paths to be processed.
    Args:
        paths: (list) The list of paths to be processed.
        file_name: (str) The name of the file to be processed.
        ext_dir: (str) The path to the folder containing the data.
        raw_dir: (str) The path to save the raw extracted data to.
    Returns:
        list: The updated list of paths to be processed.
    """
    input_path = ext_dir / Path(file_name).with_suffix(".pdf")
    output_path = raw_dir / Path(file_name).with_suffix(".json")
    assert input_path.exists(), f"Le fichier PDF n'existe pas: {input_path}"

    paths.append({"input_path": input_path, "output_path": output_path})
    (output_path).parent.mkdir(parents=True, exist_ok=True)
    return paths


def prepare_file_paths(
    tree: Dict[str, Any], ext_dir: Path, raw_dir: Path
) -> List[Dict[str, Path]]:
    """
    Prepares the file paths for the documents to be processed.
    Args:
        tree: (Dict[str, Any]) The file organisation data.
        ext_dir: (str) The path to the folder containing the data.
        raw_dir: (str) The path to save the raw extracted data to.
    Returns:
        List[Dict[str, Path]]: A list of dictionaries containing the input and output paths.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    for key, value in tree.items():
        if key == "documents_generaux":
            for doc in value:
                paths = _append_paths_dict(
                    paths=paths,
                    file_name=doc,
                    ext_dir=ext_dir,
                    raw_dir=raw_dir,
                )

        paths = _append_paths_dict(
            paths=paths, file_name=key, ext_dir=ext_dir, raw_dir=raw_dir
        )

    return paths


@app.command()
def main(
    folder: str = typer.Option("grenoble", "--folder", "-f", help="City folder"),
    ext_dir: Path = typer.Option(EXTERNAL_DATA_DIR, "--ext-dir", "-e"),
    raw_dir: Path = typer.Option(RAW_DATA_DIR, "--output-dir", "-r"),
) -> None:
    """
    Extracts data from the specified folder containing pdf files,
    converts them to text and saves it to json files with base64 images
    using Mistral OCR.

    Args:
        folder: (str) The folder containing the data.
        ext_dir: (Path) The path to the folder containing the data.
        raw_dir: (Path) The path to save the raw extracted data to.
    """
    logger.info(f"Retrieving OCR data from {ext_dir / folder}...")
    # Retrieve the list of files to be processed
    paths = prepare_file_paths(
        tree=TREE[folder],
        ext_dir=ext_dir / folder,
        raw_dir=raw_dir / folder,
    )

    for file_path in tqdm(paths, desc="OCR", total=len(paths)):
        # Get signed URL for the file then perform OCR
        signed_url = push_to_mistral(file_path=file_path["input_path"])
        ocr_response = mistral_ocr(signed_url=signed_url).model_dump()

        # Save the OCR response as JSON
        save_as_json(data=ocr_response, save_path=file_path["output_path"])

    logger.success(f"Extracting data from {ext_dir / folder} complete.")


if __name__ == "__main__":
    app()
