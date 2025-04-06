# -*- coding: utf-8 -*-
"""Pipeline from raw pdf to synthetic data.

This module provides functionality to process raw pdf files,
extract text using Mistral OCR, creating a prompt from the OCR results,
sending and retrieving the response from Gemini Pro 2.5, and converting
the final output to a readable pdf.

Version: 1.0
Date: 2025-04-05
Author: Grey Panda
"""

import json
from pathlib import Path

import typer
from google.genai import types
from loguru import logger
from PIL import Image

from src.api.gemini_thinking import gemini_api
from src.api.mistral_ocr import (
    mistral_ocr,
    push_to_mistral,
)
from src.config import (
    EXTERNAL_DATA_DIR,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
)
from src.prompt.prompt_config import CONFIG_TEMPLATE
from src.static.preprocess import Preprocess
from src.static.prompt_format import format_prompt_plu
from src.utils import save_as_json
from src.static.create_report import convert_json_to_pdf


app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def ocr(
    plu: str = typer.Argument(help="PLU to process"),
    folder: str = typer.Option("grenoble", "--folder", "-f", help="City folder"),
) -> None:
    """
    Main function to process the PDF files using Mistral OCR.
    Args:
        plu: (str) The PLU to process.
        folder: (str) The folder containing the PDF files.
    """
    input_path: Path = EXTERNAL_DATA_DIR / Path(folder) / Path(plu).with_suffix(".pdf")
    ocr_path: Path = RAW_DATA_DIR / Path(folder) / Path(plu).with_suffix(".json")

    # Check if the output file already exists
    if ocr_path.exists():
        logger.warning(f"OCR results already exists : {ocr_path}")
        logger.info("Skipping OCR for this file.")

    else:
        # Perform OCR
        signed_url = push_to_mistral(file_path=input_path)
        logger.info("Performing OCR...")
        ocr_response = mistral_ocr(signed_url=signed_url).model_dump()
        save_as_json(data=ocr_response, save_path=ocr_path)
        logger.success(f"OCR results saved to {ocr_path}.")

    preprocess = Preprocess(
        folder=folder,
        ocr_path=ocr_path,
    )
    pages_index = preprocess.get_pages()

    output_path: Path = INTERIM_DATA_DIR / Path(folder).with_suffix(".json")
    save_as_json(data=pages_index, save_path=output_path)


@app.command()
def synthesis(
    zone: str = typer.Argument(help="Zone to process in format 'Zone_UB'"),
    analysis: bool = typer.Option(
        True,
        "--analysis",
        "-a",
        help="Whether to perform analysis or not",
    ),
    regles_communes: str = typer.Option(
        "dispositions_generales",
        "--regles-communes",
        "-c",
        help="Name of the file containing the common rules",
    ),
    folder: str = typer.Option("grenoble", "--folder", "-f", help="City folder"),
    model_name: str = typer.Option(
        "gemini-2.5-pro-exp-03-25", "--model-name", "-m", help="Model name"
    ),
) -> None:
    """
    Main function to process the OCR results and generate a PDF file.
    Args:
        zone: (str) The PLU to process.
        regles_communes: (str) The name of the file containing the common rules.
        folder: (str) The folder containing the PDF files.
        model_name: (str) The model name to use for processing.
    """
    path_pages: Path = INTERIM_DATA_DIR / Path(folder).with_suffix(".json")
    pages_index = json.loads(path_pages.read_text(encoding="utf-8"))

    ocr_plu_name = pages_index[zone]["plu_name"]
    ocr_path: Path = (
        RAW_DATA_DIR / Path(folder) / Path(ocr_plu_name).with_suffix(".json")
    )

    # Extract the pages for a zone from the complete PLU
    preprocess = Preprocess(
        folder=folder,
        ocr_path=ocr_path,
    )
    preprocessed_data = preprocess.extract_pages(
        pages=pages_index[zone]["page_index"],
    )

    # If we have common rules, we need to load them and add them to the prompt
    if regles_communes:
        rc_path: Path = (
            RAW_DATA_DIR / Path(folder) / Path(regles_communes).with_suffix(".json")
        )
        assert rc_path.exists(), f"File not found: {rc_path}, did you run OCR?"

        regles_communes = json.loads(rc_path.read_text(encoding="utf-8"))
        # We then get the Parts with the common rules
        parts = format_prompt_plu(
            ocr_content=preprocessed_data,
            doc_name=ocr_plu_name.replace("_", " ").title(),
            regles_communes=regles_communes["pages"],
        )

    else:
        # Else we just get the Parts with the PLU
        parts = format_prompt_plu(
            ocr_content=preprocessed_data,
            doc_name=ocr_plu_name.replace("_", " ").title(),
        )

    logger.info(f"Processing zone: {zone}")
    assert isinstance(parts, list), f"{zone} is not of type list: {type(parts)}"
    for part in parts:
        assert isinstance(part, (types.Part, Image.Image)), (
            f"{zone} is not of type types.Part or Image.Image: {type(part)}"
        )

    output_dir = PROCESSED_DATA_DIR / Path(folder)
    output_file = (output_dir / Path(zone)).with_suffix(".json")

    if analysis:
        # Send the request to Gemini API
        response = gemini_api(
            model_name=model_name,
            contents=parts,
            generate_content_config=CONFIG_TEMPLATE,
        ).to_json_dict()

        save_as_json(
            data=response,
            save_path=output_file,
        )
        logger.success(f"File saved: {output_file}")
    else:
        # Load the response from the file
        response = json.loads(output_file.read_text(encoding="utf-8"))

    # Convert the response to PDF
    pdf_output_path: Path = output_dir / Path("pdf") / Path(zone).with_suffix(".pdf")
    convert_json_to_pdf(
        json_data=response["parsed"],
        output_pdf=str(pdf_output_path),
        margin=1.1,
        title_size=16,
    )


if __name__ == "__main__":
    app()
