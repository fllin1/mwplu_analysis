# -*- coding: utf-8 -*-
"""
This module provides functions to retrieve the source_plu_url for a given city from the
plu_processed.yaml configuration.
"""

import yaml
from loguru import logger

from src.config import CONFIG_DIR


def get_source_plu_url(city_name: str) -> str:
    """
    Retrieve the source_plu_url for a given city from the plu_processed.yaml configuration.

    Args:
        city_name (str): The name of the city

    Returns:
        str: The source PLU URL for the city, or a default URL if not found
    """
    try:
        config_file = CONFIG_DIR / "plu" / "plu_processed.yaml"
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        city_data = config.get("data", {}).get(city_name, {})
        source_url = city_data.get("source_plu_url")

        if source_url and source_url != "null":
            return source_url
        else:
            logger.warning(
                f"No source_plu_url configured for {city_name}, using default"
            )
            return "https://example.com/plu-not-configured"

    except Exception as e:
        logger.error(f"Error reading source_plu_url for {city_name}: {e}")
        return "https://example.com/plu-error"
