# -*- coding: utf-8 -*-
"""
PLU Data Loader
This script loads PLU data into a Supabase database. It processes JSON files containing PLU data,
retrieves or creates necessary records in the database, and uploads documents to a specified storage bucket.
It uses the Supabase client to interact with the database and storage, and the loguru library for logging.

Version: 1.2
Date: 2025-04-15
Author: Grey Panda
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import typer
import yaml
from loguru import logger

from src.config import PROCESSED_DATA_DIR
from supabase import Client, PostgrestAPIResponse, create_client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)


def get_or_create_ville(supabase: Client, ville_nom: str) -> str:
    """
    Get the ID of a city or creates it if it doesn't exist.

    Args:
        supabase (Client): The Supabase client.
        ville (str): The name of the city.

    Returns:
        str: The ID of the city.
    """
    result = supabase.table("villes").select("id").eq("nom", ville_nom).execute()

    if result.data and len(result.data) > 0:
        return result.data[0]["id"]

    # If the city does not exist, create it, the datetime is set by default
    insert_result = supabase.table("villes").insert({"nom": ville_nom}).execute()
    return insert_result.data[0]["id"]


def get_or_create_zonage(supabase: Client, zonage_nom: str, ville_id: str) -> str:
    """
    Get the ID of a zonage or creates it if it doesn't exist.

    Args:
        supabase (Client): The Supabase client.
        zonage_nom (str): The name of the zonage.
        ville_id (str): The ID of the city.

    Returns:
        str: The ID of the zonage.
    """
    result = (
        supabase.table("zonages")
        .select("id")
        .eq("nom", zonage_nom)
        .eq("ville_id", ville_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]["id"]

    # If the zonage does not exist, create it, the datetime is set by default
    insert_result = (
        supabase.table("zonages")
        .insert({"nom": zonage_nom, "ville_id": ville_id})
        .execute()
    )
    return insert_result.data[0]["id"]


def get_or_create_zone(supabase: Client, zone_nom: str, zonage_id: str) -> str:
    """
    Get the ID of a zone or creates it if it doesn't exist.

    Args:
        supabase (Client): The Supabase client.
        zone_nom (str): The name of the zone.
        zonage_id (str): The ID of the zonage.

    Returns:
        str: The ID of the zone.
    """
    result = (
        supabase.table("zones")
        .select("id")
        .eq("nom", zone_nom)
        .eq("zonage_id", zonage_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]["id"]

    # If the zone does not exist, create it, the datetime is set by default
    insert_result = (
        supabase.table("zones")
        .insert({"nom": zone_nom, "zonage_id": zonage_id})
        .execute()
    )
    return insert_result.data[0]["id"]


def get_or_create_typologie(supabase: Client, typologie_nom: str) -> str:
    """
    Get the ID of a typologie or creates it if it doesn't exist.

    Args:
        supabase (Client): The Supabase client.
        typologie_nom (str): The name of the typologie.

    Returns:
        str: The ID of the typologie.
    """
    result = (
        supabase.table("typologies").select("id").eq("nom", typologie_nom).execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]["id"]

    # If the typologie does not exist, create it, the datetime is set by default
    insert_result = (
        supabase.table("typologies").insert({"nom": typologie_nom}).execute()
    )
    return insert_result.data[0]["id"]


def find_existing_document(
    supabase: Client, zonage_id: str, zone_id: str, typologie_id: str
) -> Optional[str]:
    """
    Verify if a document already exists in the database.

    Args:
        supabase (Client): The Supabase client.
        zonage_id (str): The ID of the zonage.
        zone_id (str): The ID of the zone.
        typologie_id (str): The ID of the typologie.

    Returns:
        The ID of the existing document if found, otherwise None.
    """
    result = (
        supabase.table("documents")
        .select("id")
        .eq("zonage_id", zonage_id)
        .eq("zone_id", zone_id)
        .eq("typologie_id", typologie_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]["id"]
    return None


def insert_document(
    supabase: Client,
    zonage_id: str,
    zone_id: str,
    typologie_id: str,
    content: Dict[str, Any],
    plu_url: str,
    source_plu_date: str,
) -> PostgrestAPIResponse:
    """
    Insert a new document into the database.

    Args:
        supabase: The Supabase client
        zonage_id: The ID of the zonage
        zone_id: The ID of the zone
        typologie_id: The ID of the typologie
        content: The content JSON for the document
        plu_url: The URL of the PLU document
        source_plu_date: The source date of the PLU

    Returns:
        The response from the Supabase API
    """
    data = {
        "zonage_id": zonage_id,
        "zone_id": zone_id,
        "typologie_id": typologie_id,
        "content": content,
        "plu_url": plu_url,
        "source_plu_date": source_plu_date,
    }

    return supabase.table("documents").insert(data).execute()


def update_document(
    supabase: Client,
    document_id: str,
    content: Dict[str, Any],
    plu_url: str,
    source_plu_date: str,
) -> PostgrestAPIResponse:
    """
    Update an existing document.

    Args:
        supabase: The Supabase client
        document_id: The ID of the document to update
        content: The new content JSON for the document
        plu_url: The new URL of the PLU document
        source_plu_date: The new source date of the PLU

    Returns:
        The response from the Supabase API
    """
    data = {
        "content": content,
        "plu_url": plu_url,
        "source_plu_date": source_plu_date,
        "updated_at": datetime.now().isoformat(),
    }

    return supabase.table("documents").update(data).eq("id", document_id).execute()


def retrieve_public_url(supabase: Client, bucket: str, file_path: str) -> str:
    """
    Retrieve the public URL of a file in a Supabase storage bucket.

    Args:
        supabase: The Supabase client
        bucket: The name of the storage bucket
        file_path: The path to the file in the bucket

    Returns:
        The public URL of the file
    """
    return supabase.storage.from_(bucket).get_public_url(file_path)


if __name__ == "__main__":
    city = "grenoble"
    bucket = "synthesis"
    source_plu_date = "2024-07-05"
    typologie_nom = "Aucune"

    grenoble_json = {}
    data_dir = PROCESSED_DATA_DIR / city

    # Load JSON files
    for file in data_dir.glob("*.json"):
        with open(file, "r") as f:
            json_data: dict = json.loads(f.read())["parsed"]
        grenoble_json[file.stem.lower()] = json_data

    # Load the YAML file
    yaml_file_path = Path("config/plu_tree.yaml")
    with open(yaml_file_path, "r", encoding="utf-8") as f:
        tree: dict = yaml.safe_load(f)[city]

    # Get or create ville
    typer.secho(f"Processing city: {city}", fg=typer.colors.BRIGHT_RED)
    ville_id = get_or_create_ville(supabase=supabase, ville_nom=city)
    typer.secho(f"Ville ID: {ville_id}", fg=typer.colors.WHITE)

    for zonage, zones in tree.items():
        # Get or create type_zone
        typer.secho(f"Processing zonage: {zonage}", fg=typer.colors.BRIGHT_YELLOW)
        zonage_id = get_or_create_zonage(
            supabase=supabase, zonage_nom=zonage, ville_id=ville_id
        )
        typer.secho(f"Type Zone ID: {zonage_id}", fg=typer.colors.WHITE)

        for zone in zones:
            zone_lower: str = zone.lower()
            typer.secho(f"Processing zone: {zone}", fg=typer.colors.CYAN)

            # Get or create zone
            zone_id = get_or_create_zone(
                supabase=supabase, zone_nom=zone_lower, zonage_id=zonage_id
            )
            typer.secho(f"Zone ID: {zone_id}", fg=typer.colors.WHITE)

            # Get or create typologie
            typologie_id = get_or_create_typologie(
                supabase=supabase, typologie_nom=typologie_nom
            )
            typer.secho(f"Typologie ID: {typologie_id}", fg=typer.colors.WHITE)

            # Prepare document data
            json_data: dict = grenoble_json[zone_lower]
            storage_path: str = f"{city}/{zonage}/{zone.replace('zone', 'Zone')}.pdf"
            plu_url = retrieve_public_url(
                supabase=supabase, bucket=bucket, file_path=storage_path
            )

            # Check if document exists
            existing_doc_id = find_existing_document(
                supabase=supabase,
                zonage_id=zonage_id,
                zone_id=zone_id,
                typologie_id=typologie_id,
            )

            # Insert or update document
            if existing_doc_id:
                logger.info(f"Updating existing document: {existing_doc_id}")
                response = update_document(
                    supabase=supabase,
                    document_id=existing_doc_id,
                    content=json_data,
                    plu_url=plu_url,
                    source_plu_date=source_plu_date,
                )
                logger.success(f"Update response: {response.data[0]['id']}")
            else:
                logger.info("Inserting new document")
                response = insert_document(
                    supabase=supabase,
                    zonage_id=zonage_id,
                    zone_id=zone_id,
                    typologie_id=typologie_id,
                    content=json_data,
                    plu_url=plu_url,
                    source_plu_date=source_plu_date,
                )
                logger.success(f"Insert response: {response.data[0]['id']}")
