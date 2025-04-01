# -*- coding: utf-8 -*-
"""PDF OCR processor using Mistral.

This module extracts text from PDF files using Mistral OCR with base64 images,
converting the content to JSON format.

Version: 1.0
Date: 2025-03-31
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
    tree_grenoble = yaml.safe_load(f)["Grenoble"]


def prepare_file_paths(
    tree_grenoble: Dict[str, Any], ext_dir: Path, raw_dir: Path
) -> List[Dict[str, Path]]:
    """
    Prepares the file paths for the documents to be processed.
    Args:
        tree_grenoble: (Dict[str, Any]) The file organisation data.
        ext_dir: (str) The path to the folder containing the data.
        raw_dir: (str) The path to save the raw extracted data to.
    Returns:
        List[Dict[str, Path]]: A list of dictionaries containing the input and output paths.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    # Traiter les documents_generaux
    for file_name in tree_grenoble["documents_generaux"]:
        pdf_path = Path(file_name).with_suffix(".pdf")
        input_path = ext_dir / pdf_path
        assert input_path.exists(), f"Le fichier PDF n'existe pas: {input_path}"

        paths.append({"input_path": input_path, "output_path": raw_dir / pdf_path})
        (raw_dir / pdf_path).parent.mkdir(parents=True, exist_ok=True)

    # Traiter les documents_par_zone
    for zone_type, zone_names in tree_grenoble["documents_par_zone"].items():
        pdf_path = Path(zone_type).with_suffix(".pdf")
        input_path = ext_dir / pdf_path
        assert input_path.exists(), f"Le fichier PDF n'existe pas: {input_path}"

        paths.append({"input_path": input_path, "output_path": raw_dir / pdf_path})
        (raw_dir / pdf_path).parent.mkdir(parents=True, exist_ok=True)

        # Traiter les fichiers JSON des zones
        for zone_name in zone_names:
            json_path = Path(zone_type) / Path(zone_name).with_suffix(".json")
            input_path = ext_dir / json_path
            assert input_path.exists(), f"Le fichier JSON n'existe pas: {input_path}"

            paths.append({"input_path": input_path, "output_path": raw_dir / json_path})
            (raw_dir / json_path).parent.mkdir(parents=True, exist_ok=True)

    return paths


@app.command()
def main(
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
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
        tree_grenoble=tree_grenoble,
        ext_dir=ext_dir / folder,
        raw_dir=raw_dir / folder,
    )

    for file_path in tqdm(paths, desc="OCR", total=len(paths)):
        # Get signed URL for the file then perform OCR
        signed_url = push_to_mistral(file_path=file_path["input_path"])
        ocr_response = mistral_ocr(signed_url=signed_url)

        # Save the OCR response as JSON
        save_as_json(ocr_response=ocr_response, save_path=file_path["output_path"])

    logger.success(f"Extracting data from {ext_dir / folder} complete.")


if __name__ == "__main__":
    app()
