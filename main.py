# -*- coding: utf-8 -*-
"""
Main function to run the pipeline.
"""

import json

import typer
from loguru import logger

from src.config import (
    EXTERNAL_DATA_DIR,
    INTERIM_DATA_DIR,
    # PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
)
from src.mwplu.extract_pages import extract_pages_document, extract_pages_gemini
from src.mwplu.ocr import ocr_mistral
from src.utils.json import save_as_json
from src.utils.prompt_txt_to_json import convert_prompts_txt_to_json

app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def ocr(
    date_creation_source_document: str = typer.Option(
        ...,
        "--date-creation-source-document",
        "-dc",
        help="The date of the source document.",
    ),
    name_city: str = typer.Option(
        ..., "--name-city", "-nc", help="The name of the city."
    ),
    name_zoning: str = typer.Option(
        "None", "--name-zoning", "-nz", help="The name of the zoning."
    ),
    name_document: str = typer.Option(
        ..., "--name-document", "-nd", help="The name of the document."
    ),
) -> None:
    """
    Pipeline to extract pages from a PLU.
    Args:
        date_creation_source_document (str): The date of the source document (YYYY-MM-DD).
        name_city (str): The name of the city.
        name_zoning (str): The name of the zoning.
        name_document (str): The name of the document.
    """
    convert_prompts_txt_to_json()

    input_dir = EXTERNAL_DATA_DIR / name_city / date_creation_source_document
    output_dir = RAW_DATA_DIR / name_city
    if name_zoning == "None":
        input_path = input_dir / name_document
        output_path = output_dir / name_document
        output_path_backup = output_dir / date_creation_source_document / name_document
    else:
        input_path = input_dir / name_zoning / name_document
        output_path = output_dir / name_zoning / name_document
        output_path_backup = (
            output_dir / date_creation_source_document / name_zoning / name_document
        )
    input_path = input_path.with_suffix(".pdf")
    output_path = output_path.with_suffix(".json")
    output_path_backup = output_path_backup.with_suffix(".json")

    with open(input_path, mode="rb") as file:
        file_bytes = file.read()

    logger.info(f"Running OCR for {input_path.resolve()}")
    output_ocr = ocr_mistral(
        file=file_bytes,
        date_creation_source_document=date_creation_source_document,
        name_city=name_city,
        name_zoning=name_zoning,
        name_document=name_document,
    )

    save_as_json(output_ocr, output_path)
    save_as_json(output_ocr, output_path_backup)
    logger.success(f"OCR completed for {output_path.resolve()}")


@app.command()
def extract_pages(
    name_city: str = typer.Option(..., "--name-city", "-nc", help="The city name."),
    name_document: str = typer.Option(
        ..., "--name-document", "-nd", help="The name of the document."
    ),
) -> None:
    """
    Pipeline to extract pages from a PLU.
    """
    convert_prompts_txt_to_json()

    input_path = RAW_DATA_DIR / name_city / f"{name_document}.json"
    output_dir = INTERIM_DATA_DIR / name_city / name_document
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, mode="r", encoding="utf-8") as file:
        raw_data = json.load(file)

    logger.info(f"Running extract_pages_gemini for {input_path.resolve()}")
    output_extract_pages: dict = extract_pages_gemini(raw_data=raw_data)
    save_as_json(output_extract_pages, output_dir / f"{name_document}.json")

    extracted_pages: list = extract_pages_document(
        raw_data=raw_data, dict_split_pages=output_extract_pages
    )

    for data_zone in extracted_pages:
        output_path_zone = output_dir / f"{data_zone['metadata']['name_zone']}.json"
        save_as_json(data_zone, output_path_zone)
    logger.success(f"Extract_pages_gemini completed for {name_document}")


if __name__ == "__main__":
    app()
