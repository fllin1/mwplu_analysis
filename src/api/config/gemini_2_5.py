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

from src.config import API_DIR, PROMPTS_DIR


CLIENT = genai.Client(
    vertexai=True,
    project="mwplu-460919",
    location="global",
)
MODEL_PRO = "gemini-2.5-pro-preview-05-06"
MODEL_FLASH = "gemini-2.5-flash-preview-05-20"


# NOTE : Extract pages Section

with open(API_DIR / "gemini" / "response_schema_pages.json", encoding="utf-8") as file:
    response_schema_extract_pages = json.load(file)

with open(PROMPTS_DIR / "prompt_extract_zones.txt", encoding="utf-8") as file:
    PROMPT_EXTRACT_PAGES = file.read()

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
    response: dict,
    date_creation_source_document: str,
    name_city: str,
    name_document: str,
) -> dict:
    """
    Standardize the output of the Gemini API.

    Args:
        response (dict): The response from the Gemini API.
        date_creation_source_document (str): The date of the source document.
        name_city (str): The name of the city.
        name_document (str): The name of the document.
    Returns:
        dict: The standardized output.
    """
    pages = set()
    for item in response:
        pages.update(item["list_pages"])
    number_total_page = len(pages)

    metadata = {
        "type_response": "extract_pages_response",
        "name_city": name_city,
        "name_plu": name_document,
        "date_creation_source_document": date_creation_source_document,
        "number_total_page": number_total_page,
    }

    standardized_output = {
        "response": response,
        "metadata": metadata,
    }

    return standardized_output


# NOTE : Synthesis Section

path_response_schema_synthesis = API_DIR / "gemini" / "response_schema_synthesis.json"
with open(path_response_schema_synthesis, encoding="utf-8") as file:
    response_schema_synthesis = json.load(file)

with open(PROMPTS_DIR / "prompt_synthesis.txt", encoding="utf-8") as file:
    PROMPT_SYNTHESIS = file.read()

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
    response: dict,
    interim_data: dict,
) -> dict:
    """
    Standardize the output of the Gemini API.
    """
    metadata = {
        "type_response": "synthesis_response",
        "name_city": interim_data["metadata"]["name_city"],
        "name_zoning": interim_data["metadata"]["name_zoning"],
        "name_zone": interim_data["metadata"]["name_zone"],
        "name_plu": interim_data["metadata"]["name_plu"],
        "date_creation_source_document": interim_data["metadata"][
            "date_creation_source_document"
        ],
    }

    standardized_output = {
        "response": response,
        "metadata": metadata,
    }

    return standardized_output
