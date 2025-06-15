# -*- coding: utf-8 -*-
"""
Main function to run the pipeline.
"""

import json
import logging
import os

import typer
from loguru import logger
from supabase import create_client

from src.config import (
    BACKUP_DIR,
    EXTERNAL_DATA_DIR,
    IMAGES_DIR,
    INTERIM_DATA_DIR,
    PDF_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
)
from src.mwplu.extract_pages import document_zones_pages, extract_pages_gemini
from src.mwplu.generator.pdf_generator import generate_pdf_report
from src.mwplu.ocr import ocr_mistral
from src.mwplu.post_data import process_all_json_files, process_json_file
from src.mwplu.synthesis import synthesis_gemini
from src.utils.json import save_as_json
from src.utils.plu import get_references

# Configure logging to reduce verbosity
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

app = typer.Typer(pretty_exceptions_enable=False)


@app.command()
def ocr(
    date_creation: str = typer.Option(
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
        date_creation (str): The date of the source document (YYYY-MM-DD).
        name_city (str): The name of the city.
        name_zoning (str): The name of the zoning.
        name_document (str): The name of the document.
    """
    backup_dir = BACKUP_DIR / name_city / date_creation
    input_dir = EXTERNAL_DATA_DIR / name_city / date_creation
    raw_dir = RAW_DATA_DIR / name_city
    interim_dir = INTERIM_DATA_DIR / name_city

    if name_zoning == "None":
        input_path = input_dir / name_document
        output_path = raw_dir / name_document
        output_path_backup = backup_dir / name_document
    else:
        input_path = input_dir / name_zoning / name_document
        output_path = interim_dir / name_zoning / name_document
        output_path_backup = backup_dir / name_zoning / name_document

    output_path_backup = output_path_backup.with_suffix(".json")
    if output_path_backup.exists():
        logger.info(f"OCR already done for {output_path_backup.resolve()}")
        return

    input_path = input_path.with_suffix(".pdf")
    output_path = output_path.with_suffix(".json")

    with open(input_path, mode="rb") as file:
        file_bytes = file.read()

    logger.debug(
        f"Running OCR for {date_creation}, {name_city}, {name_zoning}, {name_document}"
    )

    output_ocr = ocr_mistral(
        file=file_bytes,
        date_creation_source_document=date_creation,
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
    Pipeline to extract pages from a PLU (model : gemini-2.5-flash-preview-05-20).

    Args:
        name_city (str): The name of the city.
        name_document (str): The name of the document.
    """
    input_path = RAW_DATA_DIR / name_city / f"{name_document}.json"
    output_dir = INTERIM_DATA_DIR / name_city
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, mode="r", encoding="utf-8") as file:
        raw_data = json.load(file)

    logger.info(f"Running extract_pages_gemini for {input_path.resolve()}")
    output_extract_pages: dict = extract_pages_gemini(raw_data=raw_data)
    save_as_json(output_extract_pages, output_dir / f"{name_document}.json")

    zones_pages: list = document_zones_pages(
        raw_data=raw_data, standardized_response=output_extract_pages
    )

    for data_zone in zones_pages:
        name_zoning = data_zone["metadata"]["name_zoning"]
        name_zone = data_zone["metadata"]["name_zone"]
        output_path = output_dir / name_zoning / f"{name_zone}.json"
        save_as_json(data_zone, output_path)
    logger.success(f"Extract_pages_gemini completed for {name_document}")


@app.command()
def synthesis(
    name_city: str = typer.Option(..., "--name-city", "-nc", help="The city name."),
    name_zoning: str = typer.Option(
        ..., "--name-zoning", "-nz", help="The name of the zoning."
    ),
    name_document: str = typer.Option(
        ..., "--name-document", "-nd", help="The name of the document."
    ),
    dispositions_generales: str = typer.Option(
        "None",
        "--dispositions-generales",
        "-dg",
        help="Whether to synthesize with the dispositions générales.",
    ),
) -> None:
    """
    Pipline to synthesize a PLU zone (model : gemini-2.5-pro-preview-05-06).

    Args:
        name_city (str): The name of the city.
        name_zoning (str): The name of the zoning.
        name_document (str): The name of the document.
        dispositions_generales (str): The name of the dispositions générales.
    """
    input_path = INTERIM_DATA_DIR / name_city / name_zoning / f"{name_document}.json"
    output_path = PROCESSED_DATA_DIR / name_city / name_zoning / f"{name_document}.json"

    with open(input_path, mode="r", encoding="utf-8") as file:
        interim_data = json.load(file)
        assert isinstance(interim_data, dict)

    if dispositions_generales != "None":
        path_dispositions_generales = (
            INTERIM_DATA_DIR
            / name_city
            / dispositions_generales
            / f"{dispositions_generales}.json"
        )
        with open(path_dispositions_generales, mode="r", encoding="utf-8") as file:
            dispositions_generales = json.load(file)
            assert isinstance(dispositions_generales, dict)
    else:
        dispositions_generales = None

    logger.info(f"Running synthesis_gemini for {input_path.resolve()}")
    output_synthesis: dict = synthesis_gemini(
        interim_data=interim_data, dispositions_generales=dispositions_generales
    )
    save_as_json(output_synthesis, output_path)
    logger.success(f"Synthesis completed for {name_document}")


@app.command()
def reports(
    name_city: str = typer.Option(..., "--name-city", "-nc", help="The city name."),
    name_zoning: str = typer.Option(
        ..., "--name-zoning", "-nz", help="The name of the zoning."
    ),
    name_document: str = typer.Option(
        ..., "--name-document", "-nd", help="The name of the document."
    ),
) -> None:
    """
    Generate a PDF report for a PLU zone.
    Args:
        name_city (str): The name of the city.
        name_zoning (str): The name of the zoning.
        name_document (str): The name of the document.
    """
    input_path = PROCESSED_DATA_DIR / name_city / name_zoning / f"{name_document}.json"
    assert input_path.exists()
    references = get_references(name_city)

    output_path = PDF_DIR / name_city / name_zoning / f"{name_document}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Generating PDF report for {input_path}")
    generate_pdf_report(
        json_path=str(input_path),
        logo_path=str(IMAGES_DIR / "svg" / "BLACK-MATRIX.svg"),
        references=references,
        output_path=str(output_path),
        page_logo_path=str(IMAGES_DIR / "svg" / "BLANK-MEWE.svg"),
    )


@app.command()
def upload_supabase(
    name_city: str = typer.Option(
        "all", "--name-city", "-nc", help="The name of the city ('all' for all cities)."
    ),
    name_zoning: str = typer.Option(
        "all",
        "--name-zoning",
        "-nz",
        help="The name of the zoning ('all' for all zonings).",
    ),
    name_document: str = typer.Option(
        "all",
        "--name-document",
        "-nd",
        help="The name of the document ('all' for all documents).",
    ),
) -> None:
    """
    Generate reports and upload processed PLU data to Supabase.
    This command integrates report generation with Supabase upload.

    Args:
        name_city (str): The name of the city ('all' for all cities).
        name_zoning (str): The name of the zoning ('all' for all zonings).
        name_document (str): The name of the document ('all' for all documents).
    """
    # Create Supabase client from environment variables
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return

    supabase = create_client(supabase_url, supabase_key)

    if name_city == "all":
        # First, generate reports for all processed files
        json_files = list(PROCESSED_DATA_DIR.glob("**/*.json"))

        for json_file in json_files:
            try:
                # Extract metadata from file path
                parts = json_file.relative_to(PROCESSED_DATA_DIR).parts
                if len(parts) >= 3:
                    city = parts[0]
                    zoning = parts[1]
                    document = json_file.stem

                    # Generate PDF report first
                    output_path = PDF_DIR / city / zoning / f"{document}.pdf"
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    generate_pdf_report(
                        json_path=str(json_file),
                        logo_path=str(IMAGES_DIR / "svg" / "BLACK-MATRIX.svg"),
                        references=get_references(city_name=city),
                        output_path=str(output_path),
                        page_logo_path=str(IMAGES_DIR / "svg" / "BLANK-MEWE.svg"),
                    )

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(f"Error generating report for {json_file}: {e}")

        # Then upload all data to Supabase
        process_all_json_files(supabase=supabase)

    else:
        # Process specific file(s)
        if name_zoning == "all" or name_document == "all":
            logger.error(
                "When specifying a city, you must also specify zoning and document names"
            )
            return

        json_file = (
            PROCESSED_DATA_DIR / name_city / name_zoning / f"{name_document}.json"
        )
        if not json_file.exists():
            logger.error(f"File not found: {json_file}")
            return

        # Generate PDF report first
        output_path = PDF_DIR / name_city / name_zoning / f"{name_document}.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generate_pdf_report(
            json_path=str(json_file),
            logo_path=str(IMAGES_DIR / "svg" / "BLACK-MATRIX.svg"),
            references=get_references(name_city),
            output_path=str(output_path),
            page_logo_path=str(IMAGES_DIR / "svg" / "BLANK-MEWE.svg"),
        )

        # Upload to Supabase
        logger.info(f"Uploading {json_file} to Supabase...")
        result = process_json_file(supabase=supabase, json_file_path=json_file)
        logger.success(f"✅ Uploaded document: {result['id']}")

    logger.success("🚀 Upload to Supabase completed!")


if __name__ == "__main__":
    app()
