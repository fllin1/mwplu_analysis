# -*- coding: utf-8 -*-
"""Prompt formatting utilities.

This module provides functionality to format data within a folder.
It is intended to transform the preprocessed data from `/data/interim/{folder}`
to API responses saved in the `/data/processed/{folder}`.

It includes functions to convert base64 strings to PIL images,
split text by images, and convert OCR results to parts.
The module is designed to work with Google GenAI API types and PIL images.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

import base64
import io
from typing import Any, Dict, List, Union

from google.genai import types
from PIL import Image


def base64_to_PIL(base64_str: str) -> Image.Image:
    """
    Convert a base64 string to a PIL Image.
    Args:
        base64_str (str): The base64 string to convert.
    Returns:
        Image.Image: The PIL Image.
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
        List[Union[types.Part, Image.Image]]: The list of parts.
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
        List[Union[types.Part, Image.Image]]: The list of parts.
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
    assert not len(parts) == len(ocr_result), (
        f"Parts has added no images len(output): {len(parts)}, len(input): {len(ocr_result)}"
    )
    return parts


# Format to types.Part and PIL Image for a zone
def format_prompt_plu(
    preprocessed_data: Dict[str, Dict[str, Any]],
    doc_general_name: str,
    zone_type_name: str,
    zone_name: str,
) -> List[Union[types.Part, Image.Image]]:
    """
    Convert the processed data to parts for a zone.
    Args:
        processed_data (Dict[str, Dict[str, Any]]): The processed data.
        doc_general_name (str): The name of the general document.
        zone_type_name (str): The name of the zone type.
        zone_name (str): The name of the zone.
    Returns:
        List[types.Part]: The list of parts.
    """
    string_reglement_general = f"1er document : {doc_general_name}"
    string_reglement_des_zones = f"2ème document : Réglement des {zone_type_name}"
    string_reglement_zone = f"3ème document : Réglement de la {zone_name}"

    # Convert the data to parts for document general
    parts = [types.Part.from_text(text=string_reglement_general)]
    doc_general_data = preprocessed_data["documents_generaux"][doc_general_name]
    doc_general_data_parts = ocr_result_to_parts(doc_general_data)
    parts.extend(doc_general_data_parts)

    # Convert the data to parts for zone type
    parts.append(types.Part.from_text(text=string_reglement_des_zones))
    zone_type_data = preprocessed_data["reglement_des_zones"][zone_type_name][zone_name]
    zone_type_data_parts = ocr_result_to_parts(zone_type_data)
    parts.extend(zone_type_data_parts)

    # Convert the data to parts for zone
    parts.append(types.Part.from_text(text=string_reglement_zone))
    zone_data = preprocessed_data["reglement_zone"][zone_type_name][zone_name]
    zone_data_parts = ocr_result_to_parts(zone_data)
    parts.extend(zone_data_parts)
    return parts


def format_all_prompt_plu(
    tree: Dict[str, Any], prompt: str, folder: str, preprocessed_data: Dict[str, Any]
) -> Dict[str, List[Union[types.Part, Image.Image]]]:
    """
    Format all the data for a folder.
    Args:
        tree (Dict[str, Any]): The tree of the data.
        prompt (str): The prompt to format.
        folder (str): The name of the folder.
        preprocessed_data (Dict[str, Any]): The preprocessed data.
    Returns:
        Dict[str, Any]: The formatted data.
    """
    prompts = {}

    for zone_type_name, zones_names in tree[folder]["documents_par_zone"].items():
        prompts[zone_type_name] = {}
        for zone_name in zones_names:
            # Get the data for the zone
            parts = format_prompt_plu(
                preprocessed_data=preprocessed_data,
                doc_general_name=tree[folder]["documents_generaux"][0],
                zone_type_name=zone_type_name,
                zone_name=zone_name,
            )
            prompt_plu = [types.Part.from_text(text=prompt["prompt_plu"])]
            assert isinstance(prompt_plu[0], types.Part), (
                f"{type(prompt_plu[0])} should be Part"
            )
            prompts[zone_type_name][zone_name] = prompt_plu + parts

    return prompts
