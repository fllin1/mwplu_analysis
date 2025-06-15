# -*- coding: utf-8 -*-
"""
This module provides functions to retrieve the source_plu_url for a given city from the
config/plu/references.json configuration.
"""

import json

from src.config import CONFIG_DIR


def get_references(city_name: str) -> str:
    """
    Retrieve the references for a given city from the references.json configuration.

    Args:
        city_name (str): The name of the city

    Returns:
        dict: The references for the city
    """
    config_file = CONFIG_DIR / "plu" / "references.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    global_references = config.get("mwplu", {})
    vocabulaire = global_references.get("vocabulaire")
    politiques_vente = global_references.get("politiques_vente")
    politique_confidentialite = global_references.get("politique_confidentialite")
    cgu = global_references.get("cgu")

    city_data = config.get(city_name, {})
    source_url = city_data.get("source_plu_url")

    references = {
        "source_plu_url": source_url,
        "vocabulaire": vocabulaire,
        "politiques_vente": politiques_vente,
        "politique_confidentialite": politique_confidentialite,
        "cgu": cgu,
    }

    return references
