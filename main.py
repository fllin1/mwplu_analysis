# -*- coding: utf-8 -*-
"""Pipeline from raw pdf to synthetic data.

This module provides functionality to process raw pdf files,
extract text using Mistral OCR, creating a prompt from the OCR results,
sending and retrieving the response from Gemini Pro 2.5, and converting
the final output to a readable pdf.

Usage : python main.py synthesis <zone> [options]
        <zone> : Zone to process in format 'Zone_UB'
        --analysis : Whether to perform analysis of the document with
        Gemini Pro 2.5, if not, just specify "-a".
        --regles-communes : Name of the file containing the common rules
        In this case, if there is no common rules, just specify "-c False"
        --folder : City folder
        --model-name : Model name to use for processing

Version: 1.2
Date: 2025-04-13
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
from src.static.create_report import convert_json_to_pdf
from src.static.preprocess import Preprocess
from src.static.prompt_format import format_prompt_plu
from src.utils import remove_text_outside_json, save_as_json

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
    type_zone: str = typer.Option(
        None,
        "--type-zone",
        "-t",
        help="Type of zone to process, either 'zone' or 'secteur'",
    ),
    analysis: bool = typer.Option(
        True,
        "--analysis",
        "-a",
        help="Whether to perform analysis or not",
    ),
    regles_communes: bool = typer.Option(
        True,
        "--regles-communes",
        "-r",
        help="Name of the file containing the common rules",
    ),
    city: str = typer.Option("grenoble", "--city", "-c", help="City folder"),
    file: str = typer.Option(None, "--file", "-f", help="File name"),
) -> None:
    """
    Main function to process the OCR results and generate a PDF file.
    Args:
        zone: (str) The PLU we want to process.
        regles_communes: (str) The name of the file containing the common rules.
        folder: (str) The folder containing the PDF files.
        file: (str) Corresponds to the name of the existing zone in the original document.
        model_name: (str) The model name to use for processing.
    """
    path_pages: Path = INTERIM_DATA_DIR / Path(city).with_suffix(".json")
    pages_index = json.loads(path_pages.read_text(encoding="utf-8"))
    if file is None:
        logger.info("'file' is None, using 'zone' as file")
        file = zone

    ocr_plu_name = pages_index[file]["plu_name"]
    ocr_path: Path = RAW_DATA_DIR / Path(city) / Path(ocr_plu_name).with_suffix(".json")

    # Extract the pages for a zone from the complete PLU
    preprocess = Preprocess(
        folder=city,
        ocr_path=ocr_path,
    )
    preprocessed_data = preprocess.extract_pages(
        pages=pages_index[file]["page_index"],
    )

    # If we have common rules, we need to load them and add them to the prompt
    if regles_communes:
        rc_path: Path = RAW_DATA_DIR / Path(city) / Path("dispositions_generales.json")
        if rc_path.exists():
            regles_communes = json.loads(rc_path.read_text(encoding="utf-8"))["pages"]
        else:
            assert "dispositions_generales" in pages_index, (
                f"File not found: {rc_path}, did you run OCR?"
            )
            regles_communes = preprocess.extract_pages(
                pages=pages_index["dispositions_generales"]["page_index"],
            )

        # We then get the Parts with the common rules
        parts = format_prompt_plu(
            ocr_content=preprocessed_data,
            doc_name=ocr_plu_name.replace("_", " ").title(),
            zone=zone,
            regles_communes=regles_communes,
        )

    else:
        # Else we just get the Parts with the PLU
        parts = format_prompt_plu(
            ocr_content=preprocessed_data,
            doc_name=ocr_plu_name.replace("_", " ").title(),
            zone=zone,
        )

    logger.info(f"Processing zone: {zone}")
    assert isinstance(parts, list), f"{zone} is not of type list: {type(parts)}"
    for part in parts:
        assert isinstance(part, (types.Part, Image.Image)), (
            f"{zone} is not of type types.Part or Image.Image: {type(part)}"
        )

    output_dir = PROCESSED_DATA_DIR / Path(city)
    if type_zone is not None:
        output_dir = output_dir / Path(type_zone)

    output_file = (output_dir / Path(zone)).with_suffix(".json")

    if analysis:
        # Send the request to Gemini API
        response = gemini_api(
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

    if "parsed" not in response:
        text = response["candidates"][0]["content"]["parts"][0]["text"]
        response["parsed"] = json.loads(remove_text_outside_json(text))
        save_as_json(
            data=response,
            save_path=output_file,
        )

    # Convert the response to PDF
    pdf_output_path: Path = output_dir / Path("pdf") / Path(zone).with_suffix(".pdf")

    pdf_output_path.parent.mkdir(parents=True, exist_ok=True)
    convert_json_to_pdf(
        json_data=response["parsed"],
        output_pdf=str(pdf_output_path),
        source_links={},
        margin=1.1,
        title_size=16,
    )


if __name__ == "__main__":
    app()
