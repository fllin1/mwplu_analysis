# -*- coding: utf-8 -*-
"""Functions to interact with the Mistral API for OCR processing.

This module provides utilities for OCR (Optical Character Recognition)
processing via the Mistral API.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

import base64
import os
from pathlib import Path

from mistralai import Mistral
from mistralai.models import OCRResponse

from src.config import RAW_DATA_DIR

api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)


def push_to_mistral(file_path: Path) -> str:
    """
    Pushes a file to Mistral for OCR processing.

    Args:
        file_path: The path to the file to push.

    Returns:
        The signed URL of the uploaded file.
    """
    with open(file_path, "rb") as file:
        uploaded_pdf = client.files.upload(
            file={
                "file_name": file_path.name,
                "content": file,
            },
            purpose="ocr",
        )
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    return signed_url


def mistral_ocr(signed_url: str) -> OCRResponse:
    """
    Performs OCR on the specified file.

    Args:
        signed_url: The signed URL of the file to perform OCR on.

    Returns:
        The OCR response.
    """
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True,
    )
    return ocr_response


def save_ocr_as_markdown(
    ocr_response: OCRResponse, output_dir: Path = RAW_DATA_DIR
) -> None:
    """
    Save OCR results as a markdown file with separate image files

    Args:
        ocr_response: The OCR response object.
        output_dir: The output directory to save the markdown and images.
    """
    images_dir = os.path.join(output_dir, "images")
    Path(images_dir).mkdir(parents=True, exist_ok=True)

    all_markdown = []

    for page in ocr_response.pages:
        page_markdown = page.markdown

        # Extract and save images
        for img in page.images:
            # Decode base64 image
            img_data = base64.b64decode(
                img.image_base64.split(",")[1]
                if "," in img.image_base64
                else img.image_base64
            )

            # Save image to file
            img_filename = f"{img.id}"
            img_path = os.path.join(images_dir, img_filename)
            with open(img_path, "wb") as img_file:
                img_file.write(img_data)

            # Update markdown to reference local image file
            img_rel_path = os.path.join("images", img_filename).replace("\\", "/")
            page_markdown = page_markdown.replace(
                f"![{img.id}]({img.image_base64})", f"![{img.id}]({img_rel_path})"
            )

        all_markdown.append(page_markdown)

    # Write combined markdown to file
    markdown_path = os.path.join(output_dir, "ocr_results.md")
    with open(markdown_path, "w", encoding="utf-8") as md_file:
        md_file.write("\n\n".join(all_markdown))
