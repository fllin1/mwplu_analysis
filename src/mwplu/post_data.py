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
from typing import Any, Dict

from loguru import logger
from supabase import Client

from src.api.supabase import pipeline_upload_document
from src.mwplu.generator.html_generator import generate_html_report
from src.config import HTML_DIR, PROCESSED_DATA_DIR
from src.utils.plu import get_references


def process_plu_document(
    supabase: Client,
    json_content: Dict[str, Any],
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

    logger.info(f"Processing document: {city_name}/{zoning_name}/{zone_name}")

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
        source_plu_url=get_references(city_name)["source_plu_url"],
    )
    logger.success(f"Uploaded to Supabase: {city_name}/{zoning_name}/{zone_name}")
    return result


def process_json_file(
    supabase: Client,
    json_file_path: Path,
) -> Dict[str, Any]:
    """
    Process a single JSON file.

    Args:
        supabase: The Supabase client
        json_file_path: Path to the JSON file
        source_plu_url: The source PLU URL for a city

    Returns:
        Dict[str, Any]: The inserted document data from Supabase
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_content = json.load(f)

    return process_plu_document(supabase, json_content)


def process_all_json_files(
    supabase: Client,
) -> None:
    """
    Process all JSON files in the processed directory.

    Args:
        supabase: The Supabase client
    """
    json_files = list(PROCESSED_DATA_DIR.glob("**/*.json"))
    total_files = len(json_files)

    logger.info(f"🚀 Starting bulk upload to Supabase: {total_files} files to process")

    success_count = 0
    error_count = 0

    for i, json_file_path in enumerate(json_files, 1):
        try:
            logger.info(f"📂 Processing file {i}/{total_files}: {json_file_path.name}")
            result = process_json_file(supabase=supabase, json_file_path=json_file_path)
            success_count += 1
            logger.debug(f"File {i}/{total_files} completed successfully")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                f"❌ Error processing file {i}/{total_files} ({json_file_path}): {e}"
            )
            error_count += 1

    logger.info(
        f"📊 Bulk upload completed: {success_count} successful, {error_count} failed out of {total_files} total"
    )
