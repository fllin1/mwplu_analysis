"""
Main function to POST the plu.pdf, run the OCR processing and save the response.

Version: 1.0
Date: 2025-05-23
Author: Grey Panda
"""

import os

from loguru import logger
from mistralai import Mistral

from src.api.ocr_mistral import ocr_with_mistral, push_to_mistral
from src.api.config import standardize_ocr_output
from src.utils.json import save_as_json
from src.config import BACKUP_DIR


def ocr_mistral(
    file: bytes,
    date_creation_source_document: str,
    name_city: str,
    name_zoning: str,
    name_document: str,
) -> dict:
    """
    Main function to POST the plu.pdf, run the OCR processing and save the response.
    Args:
        file (bytes): The file to push.
        date_creation_source_document (str): The date of the source document.
        name_city (str): The name of the city.
        name_document (str): The name of the document.
    Returns:
        standardized_response (dict): The standardized response.
    """

    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    signed_url = push_to_mistral(client=client, file=file, name_file=name_document)
    ocr_response = ocr_with_mistral(client=client, signed_url=signed_url)

    backup_dir = BACKUP_DIR / "raw" / name_city / date_creation_source_document
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{name_document}.json"
    save_as_json(ocr_response, backup_path)

    standardized_response = standardize_ocr_output(
        ocr_response=ocr_response,
        date_creation_source_document=date_creation_source_document,
        name_city=name_city,
        name_zoning=name_zoning,
        name_document=name_document,
    )
    return standardized_response
