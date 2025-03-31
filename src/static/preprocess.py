# -*- coding: utf-8 -*-
"""Data formatter for raw data.

This module provides functionality to format data within a folder.
It is intended to transform the preprocessed data from `/data/raw/{folder}`
into `/data/interim/{folder}`.

Be carreful to attentively respect the structure of the data and complete the
`/config/plu_tree.yaml` file as explained in the `/README.md`.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

# TODO: Add more specific docstrings on the structure of the data to all functions and classes

import json
from pathlib import Path
from typing import Any, Dict, List

from src.api.gemini_thinking import retrieve_zone_pages


class Preprocess:
    """
    Class to prepare the data for the PLU, OAP and PPRI for a specific folder.
    """

    def __init__(
        self,
        folder: str,
        raw_dir: str,
        model_name: str,
        tree: Dict[str, Any],
        prompts: Dict[str, str],
    ) -> None:
        """
        Initializes the FormatterPLU class.

        Args:
            folder: (str) The folder containing the data.
            raw_dir: (str) The path to save the raw extracted data to.
        """
        self.input_dir = raw_dir / folder
        self.tree = tree[folder]
        self.prompts = prompts
        self.model_name = model_name

    def _get_pages_reglement_des_zones(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, List[int]]]:
        """
        Retrieves the pages of the zone documents from the specific pages.
        Args:
            data (Dict[str, Any]): The data containing the pages.
        Returns:
            List[Dict[str, List[int]]]: A list of dictionaries containing the pages.
        """
        pages_dict = {}
        response = retrieve_zone_pages(
            ocr_json=data,
            prompt=self.prompts["prompt_reglement_zone"],
            model_name=self.model_name,
        )

        assert isinstance(response, list), "Response is not of type 'list'"
        for item in response:
            pages_dict[item["zone"]] = item["pages"]

        return pages_dict

    def prepare_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Prepares the data for the PLU, OAP and PPRI.
        Returns:
            Dict[str, List[Dict[str, Any]]]: The prepared data.
        """
        assert "documents_generaux" in self.tree, "'documents_generaux' not in tree"
        assert "documents_par_zone" in self.tree, "'documents_par_zone' not in tree"

        documents_generaux = {}
        reglement_des_zones = {}
        reglement_zone = {}

        # Retrieve the general documents data
        for doc in self.tree["documents_generaux"]:
            path_doc = Path(self.input_dir / doc).with_suffix(".json")

            with open(path_doc, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "pages" in data, f"Key 'pages' not in '{path_doc}'"
            documents_generaux[doc] = data["pages"]

        # Retrieve the zone documents data from the specific pages
        for zone_a in self.tree["documents_par_zone"]:
            path_par_zone = Path(self.input_dir / zone_a).with_suffix(".json")
            with open(path_par_zone, "r", encoding="utf-8") as f:
                data_zone = json.load(f)

            # Retrieve the pages of the zone documents
            pages_dict = self._get_pages_reglement_des_zones(data_zone)

            reglement_des_zones[zone_a] = {}
            for zone, pages in pages_dict.items():
                assert all(isinstance(i, int) for i in pages), (
                    f"Page index not int for '{zone_a}'"
                )
                assert all(0 <= i < len(data_zone["pages"]) for i in pages), (
                    f"Some page index are out of the document '{zone_a}'"
                )

                reglement_des_zones[zone_a][zone] = [
                    data_zone["pages"][i] for i in pages
                ]

        # Retrieve the zone documents data
        for zone_a, zones in self.tree["documents_par_zone"].items():
            reglement_zone[zone_a] = {}

            for zone in zones:
                path_zone = Path(self.input_dir / zone_a / zone).with_suffix(".json")
                with open(path_zone, "r", encoding="utf-8") as f:
                    data = json.load(f)

                assert "pages" in data, f"Key 'pages' not in '{path_zone}'"
                reglement_zone[zone_a][zone] = data["pages"]

        documents = {
            "documents_generaux": documents_generaux,
            "reglement_des_zones": reglement_des_zones,
            "reglement_zone": reglement_zone,
        }
        return documents
