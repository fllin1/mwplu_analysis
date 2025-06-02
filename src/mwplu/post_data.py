# -*- coding: utf-8 -*-
"""Pipeline Module
This module provides the main pipeline to process PLU JSON files,
generate HTML reports, and upload them to Supabase.

Version: 1.0
Date: 2025-05-25
Author: Grey Panda
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from supabase import Client

from src.api.supabase import pipeline_upload_document
from src.mwplu.generator.html_generator import generate_html_report
from src.config import HTML_DIR, PROCESSED_DATA_DIR


def process_plu_document(
    supabase: Client,
    json_content: Dict[str, Any],
    source_plu_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a PLU document: generate HTML and upload to Supabase.

    Args:
        supabase: The Supabase client
        json_content: The JSON content containing response and metadata
        source_plu_url: The URL of the source PLU

    Returns:
        Dict[str, Any]: The inserted document data from Supabase
    """
    # Extract metadata
    metadata = json_content.get("metadata", {})

    # Get required fields from metadata
    city_name = metadata.get("name_city")
    zoning_name = metadata.get("name_zoning")
    zone_name = metadata.get("name_zone")

    if not all([city_name, zoning_name, zone_name]):
        raise ValueError(
            "Missing required metadata fields: name_city, name_zoning, or name_zone"
        )

    # Generate HTML content and save it
    html_output_path = HTML_DIR / city_name / zoning_name / f"{zone_name}.html"
    html_output_path.parent.mkdir(parents=True, exist_ok=True)

    html_content = generate_html_report(json_data=json_content)
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Upload to Supabase
    result = pipeline_upload_document(
        supabase=supabase,
        content_json=json_content,
        html_content=html_content,
        source_plu_url=source_plu_url,
    )
    return result


def process_json_file(
    supabase: Client,
    json_file_path: Path,
    get_source_plu_url_func=None,
) -> Dict[str, Any]:
    """
    Process a single JSON file.

    Args:
        supabase: The Supabase client
        json_file_path: Path to the JSON file
        get_source_plu_url_func: Function to get source PLU URL for a city

    Returns:
        Dict[str, Any]: The inserted document data from Supabase
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_content = json.load(f)

    # Get source_plu_url if function is provided
    source_plu_url = None
    if get_source_plu_url_func:
        metadata = json_content.get("metadata", {})
        city_name = metadata.get("name_city")
        if city_name:
            source_plu_url = get_source_plu_url_func(city_name)
            logger.debug(f"Retrieved source_plu_url for {city_name}: {source_plu_url}")
        else:
            logger.warning(f"No city_name found in metadata for {json_file_path}")
    else:
        logger.warning(f"No get_source_plu_url_func provided for {json_file_path}")

    return process_plu_document(supabase, json_content, source_plu_url)


def process_all_json_files(
    supabase: Client,
    get_source_plu_url_func=None,
) -> None:
    """
    Process all JSON files in the processed directory.

    Args:
        supabase: The Supabase client
        get_source_plu_url_func: Function to get source PLU URL for a city
    """
    json_files = list(PROCESSED_DATA_DIR.glob("**/*.json"))

    success_count = 0
    error_count = 0

    for json_file in json_files:
        try:
            result = process_json_file(supabase, json_file, get_source_plu_url_func)
            success_count += 1
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"Error processing {json_file}: {e}")
            error_count += 1
