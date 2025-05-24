# -*- coding: utf-8 -*-
"""Functions to interact with the Mistral API for OCR processing.

This module provides utilities for OCR (Optical Character Recognition)
processing via the Mistral API.

Model version: mistral-ocr-2503-completion

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

from mistralai import Mistral
from mistralai.models import OCRResponse


def push_to_mistral(client: Mistral, file: bytes, name_file: str) -> str:
    """
    Pushes a file to Mistral for OCR processing.
    Args:
        file (bytes): The file to push.
        name_file (str): The name of the file.
    Returns:
        signed_url (str): The signed URL of the uploaded file.
    """
    uploaded_pdf = client.files.upload(
        file={
            "file_name": name_file,
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
