"""
This script extracts data from pdf files,
converts them to text and saves it to a markdown files and images.
"""

import os
from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm

from src.config import (
    EXTERNAL_DATA_DIR,
    PROCESSED_DATA_DIR,
    INTERIM_DATA_DIR,
    PROJ_ROOT,
    RAW_DATA_DIR,
)
from src.extract.clean_image import clean_images_files
from src.extract.clean_text import clean_text_files
from src.extract.mistral_ocr import (
    mistral_ocr,
    push_to_mistral,
    save_as_markdown,
)
from src.extract.utils import read_all_files_in_directory, read_all_folders_in_directory

# Create Typer app
app = typer.Typer()


@app.command()
def extract_data(
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
    ext_dir: Path = typer.Option(
        EXTERNAL_DATA_DIR, "--ext-dir", "-e", help="External directory path"
    ),
    raw_dir: Path = typer.Option(
        RAW_DATA_DIR, "--output-dir", "-r", help="Raw directory path"
    ),
):
    """
    Extracts data from the specified folder containing pdf files,
    converts them to text and saves it to markdown files and jpeg images
    using Mistral OCR.

    Parameters:
    -----------
    folder: str
        The folder containing the data.
    ext_dir: Path
        The path to the folder containing the data.
    raw_dir: Path
        The path to save the raw extracted data to.
    int_dir: Path
        The path to save the interim extracted data to.
    """
    logger.info(f"Extracting data from {ext_dir / folder}...")
    files = read_all_files_in_directory(ext_dir / folder)

    for file_path in tqdm(files, desc="Extracting files", total=len(files)):
        # Get signed URL for the file then perform OCR
        signed_url = push_to_mistral(file_path=file_path)
        ocr_response = mistral_ocr(signed_url=signed_url)

        # Save the OCR response as markdown
        save_path = raw_dir / Path(file_path).relative_to(ext_dir)
        save_path.parent.mkdir(exist_ok=True, parents=True)
        save_as_markdown(ocr_response=ocr_response, output_dir=save_path)

    logger.success(f"Extracting data from {ext_dir / folder} complete.")


@app.command()
def clean_data(
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
    raw_dir: Path = typer.Option(
        RAW_DATA_DIR, "--raw-dir", "-r", help="Raw directory path"
    ),
    int_dir: Path = typer.Option(
        INTERIM_DATA_DIR, "--int-dir", "-i", help="Interim directory path"
    ),
    ref_img_dir: Path = PROJ_ROOT / "references/images",
):
    """
    Cleans the extracted data from the specified folder containing markdown files.

    Args:
        folder: The folder containing the data.
        input_path: The path to the folder containing the data.
        output_path: The path to save the cleaned data to.
    """
    logger.info(f"Cleaning text & images from {raw_dir / folder}...")
    files = read_all_folders_in_directory(raw_dir / folder)
    os.makedirs(int_dir, exist_ok=True)

    for folder_path in tqdm(files, desc="Cleaning files", total=len(files)):
        # Create output directory
        output_path = int_dir / Path(folder_path).relative_to(raw_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        # Clean images
        if Path(folder_path).stem == "images":
            clean_images_files(
                references_dir=ref_img_dir,
                input_dir=folder_path,
                output_dir=output_path,
                threshold=5,
            )
        # Clean text
        else:
            clean_text_files(input_path=folder_path, output_dir=output_path)

    logger.success(f"Cleaning text & images from {raw_dir / folder} complete.")


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
