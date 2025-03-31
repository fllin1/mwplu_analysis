# -*- coding: utf-8 -*-
"""Functions to interact with the Gemini API.

This module provides utilities for interacting with the Gemini API
for generating content and extracting pages from documents.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

import json
import os
from typing import Any, Dict, List

from google import genai
from google.genai import types
from PIL import Image

from src.prompt.prompt_config import CONFIG_EXTRACT_PAGES


def gemini_api(
    model_name: str,
    contents: List[types.Part],
    generate_content_config: types.GenerateContentConfig,
) -> types.GenerateContentResponse:
    """
    Génère une réponse du modèle Gemini et retourne la réponse brute complète.

    Args:
        model_name: (str) Le nom du modèle à utiliser.
            models : "gemini-2.5-pro-exp-03-25", "gemini-2.0-flash"
        contents: (list) The list of contents to send to the model.
        user_message: (str) The user message to send to the model.

    Returns:
        The response from the model.
    """
    client = genai.Client(
        api_key=os.environ.get("GOOGLE_AI_API_KEY"),
    )

    for item in contents:
        assert isinstance(item, (types.Part, Image.Image)), (
            f"L'élément {item} n'est pas de type 'Part' ou 'PIL.Image.Image' : {type(item)}"
        )
    assert isinstance(generate_content_config, types.GenerateContentConfig), (
        f"generate_content_config is not of type {type(generate_content_config)}"
    )

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=generate_content_config,
    )
    return response


def retrieve_zone_pages(
    ocr_json: Dict[str, Any],
    prompt: str,
    model_name: str,
) -> Dict[str, List[int]]:
    """
    Récupère les pages du document et les affiche dans des parties séparées.

    Args:
        ocr_json: (dict) La réponse JSON brute de l'OCR.

    Returns:
        La réponse brute complète du modèle sous format dict:
        {
            "response": [
                {
                    "zone": "Nom de la première zone identifiée",
                    "pages": [12, 15, 23, 47]
                },
                {
                    "zone": "Nom de la deuxième zone identifiée",
                    "pages": [8, 19, 32]
                }
            ]
        }
    """

    assert "pages" in ocr_json, "OCR JSON does not contain pages"
    for page in ocr_json["pages"]:
        assert "markdown" in page, "OCR JSON pages do not contain markdown key"

    instruction: str = types.Part.from_text(text=prompt)
    contents: List[types.Part] = [instruction]

    for i, page in enumerate(ocr_json.get("pages")):
        contents.append(
            types.Part.from_text(
                text=json.dumps(f"page {i}: " + page["markdown"], ensure_ascii=False)
            )
        )

    response = gemini_api(
        model_name=model_name,
        contents=contents,
        generate_content_config=CONFIG_EXTRACT_PAGES,
    )

    return json.loads(response.text)["response"]
