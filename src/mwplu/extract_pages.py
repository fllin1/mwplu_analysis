# -*- coding: utf-8 -*-
"""
Extract pages from a PLU.

Version: 1.0
Date: 2025-05-24
Author: Grey Panda
"""

import json

from google.genai import types
from loguru import logger

from src.api.config.gemini_2_5 import (
    CLIENT,
    GENERATE_CONTENT_CONFIG_EXTRACT_PAGES,
    MODEL_FLASH,
    standardize_extract_pages_output,
)
from src.api.text_gemini import generate
from src.utils.logger import save_gemini_response


def extract_pages_gemini(raw_data: dict) -> dict:
    """
    Extract pages from a PLU.

    Args:
        raw_data (dict): The raw data of the PLU.
    Returns:
        standardized_response (dict): The standardized response.
    """
    parts = []

    for item in raw_data["pages"]:
        data_page = f"Page {item['number_page']} : {item['text']}"
        parts.append(types.Part(text=data_page))

    response = generate(
        client=CLIENT,
        model=MODEL_FLASH,
        parts=parts,
        generate_content_config=GENERATE_CONTENT_CONFIG_EXTRACT_PAGES,
    )
    try:
        response = json.loads(response)
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Error in extract_pages_gemini: {str(e)}")
        response = None

    save_gemini_response(
        response=response, model_name=MODEL_FLASH, operation="extract_pages"
    )

    standardized_response = standardize_extract_pages_output(
        response=response,
        date_creation_source_document=raw_data["metadata"][
            "date_creation_source_document"
        ],
        name_city=raw_data["metadata"]["name_city"],
        name_document=raw_data["metadata"]["name_document"],
    )

    return standardized_response


def extract_pages_document(raw_data: dict, dict_split_pages: dict) -> list:
    """
    Extract pages from a PLU document.

    Args:
        raw_data (dict): The raw data of the PLU.
        dict_split_pages (dict): Dictionary containing split pages information.
    Returns:
        data_zones (list): List containing extracted data zones.
    """
    data_zones = []
    for document in dict_split_pages["response"]:
        pages = [raw_data["pages"][i - 1] for i in document["list_pages"]]
        raw_metadata = raw_data["metadata"]
        metadata = {
            "type_response": "extract_pages_document",
            "name_city": raw_metadata["name_city"],
            "name_zoning": document["name_zoning"],
            "name_zone": document["name_zone"],
            "name_document": raw_metadata["name_document"],
            "date_creation_source_document": raw_metadata[
                "date_creation_source_document"
            ],
            "number_total_page": len(document["list_pages"]),
        }

        data_zone = {
            "pages": pages,
            "metadata": metadata,
        }
        data_zones.append(data_zone)

    return data_zones
