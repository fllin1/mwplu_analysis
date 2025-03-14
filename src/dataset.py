"""
This script extracts data from pdf files,
converts them to text and saves it to a markdown files and images.
"""

import sys
from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm

from src.config import EXTERNAL_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from src.extract.mistral_ocr import (
    mistral_ocr,
    push_to_mistral,
    save_as_markdown,
)
from src.extract.utils import read_all_files_in_directory

logger.remove()
logger.add(
    sys.stderr,
    format="{time} | {level} | {message}",
    level="INFO",
    backtrace=False,  # Désactive les traces détaillées
    diagnose=False,  # Désactive les informations de diagnostic
)


app = typer.Typer()


@app.command()
def extract_data(
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
    input_dir: Path = typer.Option(
        EXTERNAL_DATA_DIR, "--input-dir", "-i", help="Input directory path"
    ),
    output_dir: Path = typer.Option(
        RAW_DATA_DIR, "--output-dir", "-o", help="Output directory path"
    ),
):
    """
    Extracts data from the specified folder containing pdf files,
    converts them to text and saves it to a json files and images.

    Args:
        folder: The folder containing the data.
        input_path: The path to the folder containing the data.
        output_path: The path to save the extracted data to.
    """
    logger.info(f"Extracting data from {input_dir / folder}...")
    files = read_all_files_in_directory(input_dir / folder)

    for file in tqdm(files, desc="Extracting files", total=len(files)):
        # Get signed URL for the file then perform OCR
        signed_url = push_to_mistral(file_path=file)
        ocr_response = mistral_ocr(signed_url=signed_url)

        # Save the OCR response as markdown
        output_path = output_dir / folder / file.stem
        output_path.mkdir(parents=True, exist_ok=True)
        save_as_markdown(ocr_response=ocr_response, output_dir=output_path)

    logger.success(f"Extracting data from {input_dir / folder} complete.")


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    # ----------------------------------------------
):
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    logger.info("Processing dataset...")
    for i in tqdm(range(10), total=10):
        if i == 5:
            logger.info("Something happened for iteration 5.")
    logger.success("Processing dataset complete.")
    # -----------------------------------------


if __name__ == "__main__":
    app()
