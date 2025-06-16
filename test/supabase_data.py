# -*- coding: utf-8 -*-
"""
Supabase Data
This module provides functions to retrieve and store documents from Supabase.

Version: 1.0
Date: 2025-06-16
Author: Grey Panda
"""

import json
import os
from pathlib import Path

from supabase import Client, create_client

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")


supabase_client: Client = create_client(supabase_url, supabase_key)


def retrieve_and_store_documents(supabase: Client) -> None:
    """
    Retrieve and store documents from Supabase.

    Args:
        supabase (Client): The Supabase client.
    """
    # Fetch documents with related city, zoning, and zone names
    # Based on the schema:
    # documents -> zoning_id -> zonings -> city_id -> cities
    # documents -> zone_id -> zones
    response = (
        supabase.table("documents")
        .select(
            """
            content_json,
            zonings!documents_zoning_id_fkey(
                name,
                cities!zonings_city_id_fkey(name)
            ),
            zones!documents_zone_id_fkey(name)
            """
        )
        .execute()
    )

    if response.data:
        for document in response.data:
            content_json = document.get("content_json")
            zoning_data = document.get("zonings")
            zone_data = document.get("zones")

            if content_json and zoning_data and zone_data:
                city_name = zoning_data.get("cities", {}).get("name")
                zoning_name = zoning_data.get("name")
                zone_name = zone_data.get("name")

                if city_name and zoning_name and zone_name:
                    # Construct the output folder path
                    output_folder = Path(city_name) / zoning_name
                    output_folder.mkdir(parents=True, exist_ok=True)

                    # Construct the file path
                    file_path = output_folder / f"{zone_name}.json"

                    # Save the content_json to the file
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(content_json, f, indent=4, ensure_ascii=False)
                        print(f"Successfully saved {file_path}")
                    except IOError as e:
                        print(f"Error saving file {file_path}: {e}")
                else:
                    print(
                        f"Missing city, zoning, or zone name for a document: {document}"
                    )
            else:
                print(
                    f"Missing content_json, zoning, or zone data for a document: {document}"
                )
    else:
        print("No documents found or an error occurred while fetching.")
        if hasattr(response, "error") and response.error:
            print(f"Supabase error: {response.error}")


if __name__ == "__main__":
    retrieve_and_store_documents(supabase_client)
