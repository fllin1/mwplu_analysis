# -*- coding: utf-8 -*-
"""Config to use Gemini 2.5 Pro Preview 05-06.

Expected format for further analysis.
./references/api/gemini/pages_output.json

Model pro: gemini-2.5-pro-preview-05-06
Model flash: gemini-2.5-flash-preview-05-20

Version: 1.0
Date: 2025-05-23
Author: Grey Panda
"""

import json

from google import genai
from google.genai import types

from src.config import REFERENCES_DIR


CLIENT = genai.Client(
    vertexai=True,
    project="urbandocs",
    location="global",
)
MODEL_PRO = "gemini-2.5-pro-preview-05-06"
MODEL_FLASH = "gemini-2.5-flash-preview-05-20"

# Extract pages

pages_path = REFERENCES_DIR / "api" / "gemini" / "response_schema_pages.json"
with open(pages_path, encoding="utf-8") as file:
    response_schema_extract_pages = json.load(file)

GENERATE_CONTENT_CONFIG_EXTRACT_PAGES = types.GenerateContentConfig(
    temperature=1,
    top_p=1,
    seed=0,
    max_output_tokens=65535,
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
        ),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
    ],
    response_mime_type="application/json",
    response_schema=response_schema_extract_pages,
)


def standardize_extract_pages_output(
    response: str,
    date_creation_source_document: str,
    name_city: str,
    name_document: str,
) -> dict:
    """
    Standardize the output of the Gemini API.
    """
    pages = set()
    for item in response:
        pages.update(item["list_pages"])
    number_total_page = len(pages)

    metadata = {
        "type_response": "extract_pages_response",
        "name_city": name_city,
        "name_document": name_document,
        "date_creation_source_document": date_creation_source_document,
        "number_total_page": number_total_page,
    }

    standardized_output = {
        "response": response,
        "metadata": metadata,
    }

    return standardized_output


# Synthesis

synthesis_path = REFERENCES_DIR / "api" / "gemini" / "response_schema_plu.json"
with open(synthesis_path, encoding="utf-8") as file:
    response_schema_synthesis = json.load(file)

GENERATE_CONTENT_CONFIG_SYNTHESIS = types.GenerateContentConfig(
    temperature=1,
    top_p=1,
    seed=0,
    max_output_tokens=65535,
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
        ),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
    ],
    response_mime_type="application/json",
    response_schema=response_schema_synthesis,
)


def standardize_synthesis_output(
    response: str,
    date_creation_source_document: str,
    name_city: str,
    name_document: str,
) -> dict:
    """
    Standardize the output of the Gemini API.
    """
    response_json = json.loads(response)

    metadata = {
        "type_response": "synthesis_response",
        "name_city": name_city,
        "name_document": name_document,
        "date_creation_source_document": date_creation_source_document,
    }

    standardized_output = {
        "response": response_json,
        "metadata": metadata,
    }

    return standardized_output
