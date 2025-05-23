# -*- coding: utf-8 -*-
"""Prompt formatting utilities.

This module provides functionality to format data within a folder.
It is intended to transform the preprocessed data from `/data/interim/{folder}`
to API responses saved in the `/data/processed/{folder}`.

It includes functions to convert base64 strings to PIL images,
split text by images, and convert OCR results to parts.
The module is designed to work with Google GenAI API types and PIL images.

Version: 1.0
Date: 2025-04-05
Author: Grey Panda
"""

import base64
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from google.genai import types
from PIL import Image
from loguru import logger

from src.config import PROJ_ROOT

# Loading the prompts
PROMPT_PATH: Path = PROJ_ROOT / Path("config/prompts.json")
prompts: Dict[str, str] = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))


def base64_to_PIL(base64_str: str) -> Image.Image:
    """
    Convert a base64 string to a PIL Image.
    Args:
        base64_str (str): The base64 string to convert.
    Returns:
        image (Image.Image): The PIL Image.
    """
    image_data = base64.b64decode(base64_str.split(",")[1])
    assert isinstance(image_data, bytes), f"{image_data} not bytes: {type(image_data)}"

    image = Image.open(io.BytesIO(image_data))
    assert isinstance(image, Image.Image), f"{image} not a PIL Image: {type(image)}"

    return image


# Format to types.Part and PIL Image for a page
def split_text_by_image(
    text: str, images: List[str]
) -> List[Union[types.Part, Image.Image]]:
    """
    Split the text by the images from the data of a page.
    Args:
        text (str): The text to split.
        images (List[str]): The images to split the text by.
    Returns:
        parts (List[Union[types.Part, Image.Image]]): Parts for one page.
    """
    parts = []
    # Check if there are images
    if images:
        for image in images:
            image_name = image["id"]
            image_pil = base64_to_PIL(image["image_base64"])
            assert isinstance(image_pil, Image.Image), (
                f"{image_pil} is not a PIL Image: {type(image_pil)}"
            )

            text_list = text.split(f"![{image_name}]({image_name})")
            assert len(text_list) == 2, (
                f"Text split by image {image_name} failed: {text_list}"
            )
            text = text_list[1]

            parts.append(types.Part.from_text(text=text_list[0]))
            parts.append(image_pil)
        parts.append(types.Part.from_text(text=text))
        return parts

    else:
        return [types.Part.from_text(text=text)]


# Format to types.Part and PIL Image for a document
def ocr_result_to_parts(
    ocr_result: List[Dict[int, Any]],
) -> List[Union[types.Part, Image.Image]]:
    """
    Convert the OCR result to parts for a page.
    Args:
        ocr_result (List[Dict[int, Any]]): The OCR result.
    Returns:
        parts (List[Union[types.Part, Image.Image]]): Parts for one document.
    """
    parts = []
    for page_data in ocr_result:
        text = f"page {page_data['index'] + 1}: " + page_data["markdown"]
        assert isinstance(text, str), f"{text} is not a string: {type(text)}"

        images = page_data["images"]
        assert isinstance(images, list), f"{images} is not a list: {type(images)}"

        page_parts = split_text_by_image(text=text, images=images)
        parts.extend(page_parts)

    assert len(parts) >= len(ocr_result), "Parts has less elements than expected"
    if len(parts) == len(ocr_result):
        logger.warning("Parts has added no images")
    return parts


# Format to types.Part and PIL Image for a zone
def format_prompt_plu(
    ocr_content: Dict[str, Any],
    doc_name: List[str],
    zone: str,
    regles_communes: Optional[Dict[str, Any]] = None,
    prompts: str = prompts,
) -> List[Union[types.Part, Image.Image]]:
    """
    Convert the processed data to parts for a zone.
    Args:
        ocr_content (Dict[str, Any]): The processed data.
        doc_name (List[str]): The name of the document.
        regles_communes (Optional[Dict[str, Any]]): The common rules to format.
        prompts (str): The prompts to format.
    Returns:
        parts (List[Union[types.Part, Image.Image]]): The list of parts.
    """
    prompt = prompts["prompt_plu"].format(ZONE_CADASTRALE_CIBLE=zone)
    parts = [types.Part.from_text(text=prompt)]

    if regles_communes:
        parts_communes = [
            types.Part.from_text(text="Nom du document : Règles communes")
        ]
        com_content_parts = ocr_result_to_parts(regles_communes)
        parts_communes.extend(com_content_parts)
        logger.info("Processing common rules...")

        parts.extend(parts_communes)
        assert len(parts) >= len(parts_communes), (
            "Had the common rules been added to the parts?"
        )

    parts_zone = [types.Part.from_text(text=f"Nom du document : {doc_name} - {zone}")]
    zone_content_parts = ocr_result_to_parts(ocr_content)
    parts_zone.extend(zone_content_parts)
    logger.info("Processing zone...")

    parts.extend(parts_zone)

    return parts


def format_all_prompt_plu(
    documents: Dict[str, Dict[str, Any]],
    regles_communes: Optional[Dict[str, Any]] = None,
    prompts: str = prompts,
) -> Dict[str, List[Union[types.Part, Image.Image]]]:
    """
    Format all the data for a folder.
    Args:
        documents (Dict[str, Dict[str, Any]]): The documents to format.
        regles_communes (Optional[Dict[str, Any]]): The common rules to format.
        prompts (str): The prompts to format.
    Returns:
        prompts (Dict[str, List[Union[types.Part, Image.Image]]]): The formatted data.
    """
    prompts = {}

    for zone_name, document in documents.items():
        if regles_communes:
            # Get the data for the zone and the common rules
            parts = format_prompt_plu(
                ocr_content=document,
                doc_name=zone_name,
                regles_communes=regles_communes,
            )
        else:
            # Get the data for the zone
            parts = format_prompt_plu(
                ocr_content=document,
                doc_name=zone_name,
            )

        prompts[zone_name].extend(parts)
    return prompts
