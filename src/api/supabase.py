# -*- coding: utf-8 -*-
"""
Supabase API
This module provides functions to interact with the Supabase database.

Version: 1.2
Date: 2025-05-28
Author: Grey Panda
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from supabase import Client

from src.config import LOGS_DIR, PDF_DIR
from src.utils.path_bucket import normalize_path


def get_or_create_city(supabase: Client, city_name: str) -> str:
    """
    Get or create a city in the database.

    Args:
        supabase (Client): The Supabase client.
        city_name (str): The name of the city.
    """
    result = supabase.table("cities").select("id").eq("name", city_name).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]["id"]
    insert_result = supabase.table("cities").insert({"name": city_name}).execute()
    return insert_result.data[0]["id"]


def get_or_create_zoning(supabase: Client, zoning_name: str, city_id: str) -> str:
    """
    Get or create a zoning in the database.

    Args:
        supabase (Client): The Supabase client.
        zoning_name (str): The name of the zoning.
        city_id (str): The id of the city.
    """
    result = (
        supabase.table("zonings")
        .select("id")
        .eq("name", zoning_name)
        .eq("city_id", city_id)
        .execute()
    )
    if result.data and len(result.data) > 0:
        return result.data[0]["id"]
    insert_result = (
        supabase.table("zonings")
        .insert({"name": zoning_name, "city_id": city_id})
        .execute()
    )
    return insert_result.data[0]["id"]


def get_or_create_zone(
    supabase: Client,
    zone_name: str,
    zoning_id: str,
    zones_constructibles: Optional[bool] = None,
) -> str:
    """
    Get or create a zone in the database.

    Args:
        supabase (Client): The Supabase client.
        zone_name (str): The name of the zone.
        zoning_id (str): The id of the zoning.
        zones_constructibles (Optional[bool]): Whether the zone is constructible.
    """
    result = (
        supabase.table("zones")
        .select("id")
        .eq("name", zone_name)
        .eq("zoning_id", zoning_id)
        .execute()
    )
    if result.data and len(result.data) > 0:
        zone_id = result.data[0]["id"]
        # Update zones_constructibles if provided and different
        if zones_constructibles is not None:
            supabase.table("zones").update(
                {"zones_constructibles": zones_constructibles}
            ).eq("id", zone_id).execute()
        return zone_id

    # Create new zone with zones_constructibles field
    zone_data = {"name": zone_name, "zoning_id": zoning_id}
    if zones_constructibles is not None:
        zone_data["zones_constructibles"] = zones_constructibles

    insert_result = supabase.table("zones").insert(zone_data).execute()
    return insert_result.data[0]["id"]


def get_or_create_typology(supabase: Client, typology_name: str) -> str:
    """
    Get or create a typology in the database.

    Args:
        supabase (Client): The Supabase client.
        typology_name (str): The name of the typology.
    """
    result = (
        supabase.table("typologies").select("id").eq("name", typology_name).execute()
    )
    if result.data and len(result.data) > 0:
        return result.data[0]["id"]
    insert_result = (
        supabase.table("typologies").insert({"name": typology_name}).execute()
    )
    return insert_result.data[0]["id"]


def upload_pdf_to_storage(
    supabase: Client, local_pdf_path: Path, storage_path: Path, bucket: str = "pdfs"
) -> Optional[str]:
    """
    Upload a PDF file to the storage. If it exists, it will be replaced.

    Args:
        supabase (Client): The Supabase client.
        local_pdf_path (Path): The path to the local PDF file.
        storage_path (Path): The path to the storage (e.g., city/zoning/zone.pdf).
        bucket (str): The name of the bucket.

    Returns:
        Optional[str]: The storage path of the uploaded file, or None if upload fails.
    """
    if not local_pdf_path.exists():
        logger.error(f"PDF file not found: {local_pdf_path}")
        return None

    log_dir = LOGS_DIR / "post_data"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_filename = log_dir / f"{storage_path.stem}_upload_response.log"

    try:
        # Normalize storage path for Supabase (e.g. "city/zoning/zone.pdf")
        normalized_storage_path = (
            normalize_path(storage_path.parent.as_posix()) + "/" + storage_path.name
        )

        with open(local_pdf_path, "rb") as f:
            res = supabase.storage.from_(bucket).upload(
                path=normalized_storage_path,
                file=f,
                file_options={"content-type": "application/pdf", "upsert": "true"},
            )

        with open(log_filename, "w", encoding="utf-8") as log_file:
            log_file.write(str(res))

        # Check if upload was successful
        # The response might be an UploadResponse object or a dict
        if hasattr(res, "status_code") and res.status_code == 200:
            return normalized_storage_path
        elif isinstance(res, dict) and (res.get("id") or res.get("Key")):
            return normalized_storage_path
        elif hasattr(res, "path") and res.path:
            # UploadResponse object with path indicates success
            return normalized_storage_path
        elif hasattr(res, "fullPath") and res.fullPath:
            # UploadResponse object with fullPath indicates success
            return normalized_storage_path
        else:
            logger.error(f"Upload response does not indicate success: {res}")
            return None

    except Exception as e:
        logger.error(
            f"Error uploading PDF {local_pdf_path} to {bucket}/{normalized_storage_path}: {e}"
        )
        return None


def find_existing_document(
    supabase: Client, zoning_id: str, zone_id: str, typology_id: str
) -> Optional[str]:
    """
    Find an existing document by zoning_id, zone_id, and typology_id.

    Args:
        supabase: The Supabase client.
        zoning_id: The ID of the zoning.
        zone_id: The ID of the zone.
        typology_id: The ID of the typology.

    Returns:
        The ID of the existing document if found, otherwise None.
    """
    try:
        result = (
            supabase.table("documents")
            .select("id")
            .eq("zoning_id", zoning_id)
            .eq("zone_id", zone_id)
            .eq("typology_id", typology_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Error finding existing document: {e}")
        return None


def update_document_in_db(
    supabase: Client,
    document_id: str,
    content_json: Dict[str, Any],
    html_content: str,
    pdf_storage_path: Optional[str],
    source_plu_url: Optional[str],
    source_plu_date: Optional[str],
) -> Dict[str, Any]:
    """
    Update an existing document in the database.

    Args:
        supabase: The Supabase client.
        document_id: The ID of the document to update.
        content_json: The JSON content.
        html_content: The HTML content.
        pdf_storage_path: The path to the PDF in storage.
        source_plu_url: The URL of the source PLU.
        source_plu_date: The date of the source PLU.

    Returns:
        The updated document data.
    """
    data_to_update = {
        "content_json": content_json,
        "html_content": html_content,
        "pdf_storage_path": pdf_storage_path,
        "source_plu_url": source_plu_url,
        "source_plu_date": source_plu_date,
        "updated_at": datetime.now().isoformat(),
    }
    result = (
        supabase.table("documents")
        .update(data_to_update)
        .eq("id", document_id)
        .execute()
    )
    if result.data:
        return result.data[0]
    logger.error(
        f"Failed to update document with id: {document_id}. Response: {result}"
    )


def insert_document(
    supabase: Client,
    zoning_id: str,
    zone_id: str,
    typology_id: str,
    content_json: Dict[str, Any],
    html_content: str,
    pdf_storage_path: Optional[str],
    source_plu_url: Optional[str],
) -> Dict[str, Any]:
    """
    Insert or update a document in the database.
    If a document with the same zoning_id, zone_id, and typology_id exists, it's updated.
    Otherwise, a new document is inserted.

    Args:
        supabase (Client): The Supabase client.
        zoning_id (str): The id of the zoning.
        zone_id (str): The id of the zone.
        typology_id (str): The id of the typology.
        content_json (Dict[str, Any]): The content of the document.
        html_content (str): The HTML content of the document.
        pdf_storage_path (Optional[str]): The path to the PDF file in the storage.
        source_plu_url (Optional[str]): The URL of the source PLU.

    Returns:
        Dict[str, Any]: The inserted or updated document data.
    """
    metadata = content_json.get("metadata", {})
    source_plu_date = metadata.get("date_creation_source_document")

    existing_document_id = find_existing_document(
        supabase, zoning_id, zone_id, typology_id
    )

    if existing_document_id:
        return update_document_in_db(
            supabase,
            existing_document_id,
            content_json,
            html_content,
            pdf_storage_path,
            source_plu_url,
            source_plu_date,
        )

    data_to_insert = {
        "zoning_id": zoning_id,
        "zone_id": zone_id,
        "typology_id": typology_id,
        "content_json": content_json,
        "html_content": html_content,
        "pdf_storage_path": pdf_storage_path,
        "source_plu_url": source_plu_url,
        "source_plu_date": source_plu_date,
    }
    result = supabase.table("documents").insert(data_to_insert).execute()
    if result.data:
        return result.data[0]

    logger.error(f"Failed to insert new document. Response: {result}")


def pipeline_upload_document(
    supabase: Client,
    content_json: Dict[str, Any],
    html_content: str,
    source_plu_url: Optional[str] = None,
    bucket: str = "pdfs",
) -> Dict[str, Any]:
    """
    Pipeline to upload a PLU to the database.

    Args:
        supabase (Client): The Supabase client.
        content_json (Dict[str, Any]): The content of the document.
        html_content (str): The HTML content of the document.
        source_plu_url (Optional[str]): The URL of the source PLU.
        bucket (str): The name of the bucket.

    Returns:
        Dict[str, Any]: The inserted document data.
    """
    metadata = content_json.get("metadata", {})
    name_city = metadata.get("name_city")
    name_zoning = metadata.get("name_zoning")
    name_zone = metadata.get("name_zone")
    name_typology = metadata.get("name_typology", "Aucune")
    zones_constructibles = metadata.get("zones_constructibles")

    # Get or create all related entities
    city_id = get_or_create_city(supabase, name_city)
    zoning_id = get_or_create_zoning(supabase, name_zoning, city_id)
    zone_id = get_or_create_zone(supabase, name_zone, zoning_id, zones_constructibles)
    typology_id = get_or_create_typology(supabase, name_typology)

    # Upload PDF to storage
    storage_path = Path(f"{name_city}/{name_zoning}/{name_zone}.pdf")
    pdf_local_path = PDF_DIR / storage_path
    if not pdf_local_path.exists():
        logger.warning(f"PDF file not found at: {pdf_local_path}")

    pdf_storage_path = upload_pdf_to_storage(
        supabase=supabase,
        local_pdf_path=pdf_local_path,
        storage_path=storage_path,
        bucket=bucket,
    )

    # Insert or update document in the database
    document_data = insert_document(
        supabase=supabase,
        zoning_id=zoning_id,
        zone_id=zone_id,
        typology_id=typology_id,
        content_json=content_json,
        html_content=html_content,
        pdf_storage_path=pdf_storage_path,
        source_plu_url=source_plu_url,
    )

    return document_data
