# -*- coding: utf-8 -*-

import json
from typing import List, Union

from google.genai import types
from loguru import logger
from PIL import Image

from src.api.config.gemini_2_5 import (
    CLIENT,
    GENERATE_CONTENT_CONFIG_SYNTHESIS,
    MODEL_PRO,
    PROMPT_SYNTHESIS,
    standardize_synthesis_output,
)
from src.api.text_gemini import generate
from src.utils.image import base64_to_image


def data_to_parts(interim_data: dict) -> List[Union[types.Part, Image.Image]]:
    """
    Convert the data of the zone to parts for the synthesis.

    Args:
        interim_data (dict): The data of the zone.
    Returns:
        parts (list): The parts for the synthesis.
    """
    parts = []

    for page in interim_data["pages"]:
        number_page = types.Part.from_text(text=f"Page numéro : {page['number_page']}")
        text = types.Part.from_text(text=page["text"])
        parts.extend([number_page, text])

        images = page["images"]
        if not images:
            continue
        for image in images:
            name_image = types.Part(text=f"ID de l'image : {image['name_img']}")
            image_pil = base64_to_image(image["image_base64"])
            parts.extend([name_image, image_pil])

    return parts


def synthesis_parts(
    interim_data: dict, dispositions_generales: Union[dict, None] = None
) -> List[Union[types.Part, Image.Image]]:
    """
    Add the dispositions générales to the data of the zone if it exists.

    Args:
        interim_data (dict): The data of the zone.
        dispositions_generales (dict): The dispositions générales (optional).
    Returns:
        parts (list): The parts for the synthesis.
    """
    metadata = interim_data["metadata"]

    context_prompt = f"""
    {PROMPT_SYNTHESIS.format(ZONE_CADASTRALE_CIBLE=metadata["name_zone"])}
    ------------------------------
    PLU de la ville de {metadata["name_city"]}
    et de la catégorie générale {metadata["name_zoning"]}
    """

    parts = [types.Part.from_text(text=context_prompt)]

    parts_zone = data_to_parts(interim_data=interim_data)
    parts.extend(parts_zone)

    if dispositions_generales:
        context_prompt_generales = f"""
        ------------------------------
        Dispositions générales du PLU de la ville de {metadata["name_city"]}
        """
        parts.extend([types.Part.from_text(text=context_prompt_generales)])
        parts_generales = data_to_parts(interim_data=dispositions_generales)
        parts.extend(parts_generales)

    return parts


def synthesis_gemini(
    interim_data: dict, dispositions_generales: Union[dict, None] = None
) -> dict:
    """
    Synthesis the PLU using Gemini.

    Args:
        interim_data (dict): The data of the zone.
        dispositions_generales (dict): The dispositions générales (optional).
    Returns:
        standardized_response (dict): The standardized response.
    """
    parts = synthesis_parts(
        interim_data=interim_data,
        dispositions_generales=dispositions_generales,
    )
    response = generate(
        client=CLIENT,
        model=MODEL_PRO,
        parts=parts,
        generate_content_config=GENERATE_CONTENT_CONFIG_SYNTHESIS,
    )

    try:
        response_json = json.loads(response.text)
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Error in extract_pages_gemini: {str(e)}")
        response_json = None

    standardized_response = standardize_synthesis_output(
        response=response_json,
        interim_data=interim_data,
    )

    return standardized_response
