# -*- coding: utf-8 -*-
"""Functions to interact with the Gemini API.

This module provides utilities for interacting with the Gemini API
for generating content.

Version: 1.0
Date: 2025-05-23
Author: Grey Panda
"""

from typing import Generator

from google import genai
from google.genai import types


def generate(
    client: genai.Client,
    model: str,
    parts: list[types.Part],
    generate_content_config: types.GenerateContentConfig,
) -> Generator[str, None, None]:
    """
    Generate content with Gemini API.
    Args:
        client (genai.Client): The client to use.
        model (str): The model to use.
        parts (list[types.Part]): The parts to use.
        generate_content_config (types.GenerateContentConfig): The config to use.
    Returns:
        Generator[str, None, None]: The generator of the content.
    """
    contents = [types.Content(role="user", parts=parts)]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    return response.text


def generate_stream(
    client: genai.Client,
    model: str,
    parts: list[types.Part],
    generate_content_config: types.GenerateContentConfig,
) -> Generator[str, None, None]:
    """
    Generate content with Gemini API.
    """
    contents = [types.Content(role="user", parts=parts)]
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        yield chunk.text
