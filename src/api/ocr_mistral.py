# -*- coding: utf-8 -*-
"""Functions to interact with the Mistral API for OCR processing.

This module provides utilities for OCR (Optical Character Recognition)
processing via the Mistral API.

Model version: mistral-ocr-2503-completion

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

import os
from pathlib import Path
from datetime import date

from mistralai import Mistral
from mistralai.models import OCRResponse

from src.api.utils import standardize_ocr_output
from src.utils.json import save_as_json


def push_to_mistral(client: Mistral, path_input: Path) -> str:
    """
    Pushes a file to Mistral for OCR processing.
    Args:
        file_path (Path): The path to the file to push.
    Returns:
        signed_url (str): The signed URL of the uploaded file.
    """
    with open(path_input, "rb") as file:
        uploaded_pdf = client.files.upload(
            file={
                "file_name": path_input.name,
                "content": file,
            },
            purpose="ocr",
        )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    return signed_url


def ocr_with_mistral(client: Mistral, signed_url: str) -> OCRResponse:
    """
    Performs OCR on the specified file.
    Args:
        signed_url(str): The signed URL of the file to perform OCR on.
    Returns:
        ocr_response(OCRResponse): The OCR response.
    """
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True,
    )
    return ocr_response.model_dump()


def main(
    path_input: Path,
    path_output: Path,
    date_creation_source_document: date.isoformat,
    name_city: str,
    name_document: str,
) -> None:
    """
    Main function to POST the plu.pdf, run the OCR processing and save the response.
    """
    api_key = os.environ["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)

    signed_url = push_to_mistral(client=client, path_input=path_input)
    ocr_response = ocr_with_mistral(client=client, signed_url=signed_url)
    standardized_response = standardize_ocr_output(
        ocr_response=ocr_response,
        date_creation_source_document=date_creation_source_document,
        name_city=name_city,
        name_document=name_document,
    )
    save_as_json(standardized_response, path_output)
