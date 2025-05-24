# -*- coding: utf-8 -*-
"""Convert base64 string to PIL Image.

This module provides a utility function to convert a base64 string
to a PIL Image.

Version: 1.0
Date: 2025-04-05
Author: Grey Panda
"""

import base64
import io

from PIL import Image


def base64_to_image(base64_str: str) -> Image.Image:
    """
    Convert a base64 string to a PIL Image.
    Args:
        base64_str (str): The base64 string to convert.
    Returns:
        image (Image.Image): The PIL Image.
    """
    image_data = base64.b64decode(base64_str)
    assert isinstance(image_data, bytes), f"{image_data} not bytes: {type(image_data)}"
    image = Image.open(io.BytesIO(image_data))
    assert isinstance(image, Image.Image), f"{image} not a PIL Image: {type(image)}"
    return image
