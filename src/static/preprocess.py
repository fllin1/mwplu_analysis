# -*- coding: utf-8 -*-
"""Data formatter for raw data.

This module provides functionality to format data within a folder.
It is intended to transform the preprocessed data from `/data/raw/{folder}`
into `/data/interim/{folder}`.

Be carreful to attentively respect the structure of the data and complete the
`/config/plu_tree.yaml` file as explained in the `/README.md`.

Version: 1.1
Date: 2025-04-05
Author: Grey Panda
"""

# TODO: Add more specific docstrings on the structure of the data to all functions and classes

import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from src.api.gemini_thinking import retrieve_zone_pages
from src.static.pdf import extract
from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR, PROJ_ROOT


# Loading the prompts
PROMPT_PATH: Path = PROJ_ROOT / Path("config/prompts.json")
PROMPTS: Dict[str, str] = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))


class Preprocess:
    """
    Class to prepare the data for the PLU, OAP and PPRI for a specific folder.
    """

    def __init__(
        self,
        folder: str,
        ocr_path: Path,
        model_name: str = "gemini-2.5-pro-exp-03-25",
        prompts: Dict[str, str] = PROMPTS,
    ) -> None:
        """
        Initializes the FormatterPLU class.
        Args:
            folder: (str) The folder containing the data.
            model_name: (str) The name of the model to use.
            tree: (Dict[str, Any]) The tree structure of the data.
            prompts: (Dict[str, str]) The prompts to use for the data.
        """
        # Set the directories for the raw, interim and processed data
        self.raw_dir = RAW_DATA_DIR / folder
        self.int_dir = INTERIM_DATA_DIR

        self.folder = folder
        self.model_name = model_name
        self.prompts = prompts
        self.ocr_path = ocr_path
        self.ocr_plu = json.loads(ocr_path.read_text(encoding="utf-8"))

    def _get_pages_reglement_des_zones(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, List[int]]]:
        """
        Retrieves the pages of the zone documents from the specific pages.
        Args:
            data (Dict[str, Any]): The data containing the pages.
        Returns:
            List[Dict[str, List[Any]]]: A list of dictionaries containing
            the documents references and the pages.
        """
        response = retrieve_zone_pages(
            ocr_json=data,
            prompt=self.prompts["prompt_reglement_zone"],
            model_name=self.model_name,
        )
        assert isinstance(response, list), "Response is not of type 'list'"

        return response

    def get_pages(self) -> List[Dict[str, Any]]:
        """
        Retrieves the pages of the zone documents from the specific pages.
        Returns:
            pages_zones (List[Dict[str, Any]]): The prepared data.
        """
        path_pages: Path = self.int_dir / Path(self.folder).with_suffix(".json")
        if not path_pages.exists():
            pages_zones = {}
        else:
            pages_zones = json.loads(path_pages.read_text(encoding="utf-8"))

        plu_name = self.ocr_path.stem

        # Retrieve the pages of the zone documents
        response: list = self._get_pages_reglement_des_zones(self.ocr_plu)
        logger.info(f"Pages retrieved : {plu_name}")

        for zones in response:
            assert all(isinstance(page, int) for page in zones["pages"]), (
                f"Page index not int for '{plu_name}, {zones}'"
            )
            assert all(
                0 <= i <= self.ocr_plu["usage_info"]["pages_processed"]
                for i in zones["pages"]
            ), f"Some page index are out of the document '{plu_name}'"
            assert isinstance(zones["zone"], list), (
                f"{zones['zone']} is not of type 'list' for '{plu_name}'"
            )

            # For each zone, add the pages to the documents_pages dictionary
            # And create sub-pdf from the original pdfs according to the pages
            for zone in zones["zone"]:
                pages_zones[zone] = {"page_index": zones["pages"], "plu_name": plu_name}
                try:
                    extract(
                        folder=self.folder,
                        input_pdf=Path(plu_name),
                        output_pdf=Path(zone),
                        pages=zones["pages"],
                    )
                except IndexError:
                    logger.error(
                        f"Error extracting pages {zones['pages']} from {plu_name} for zone {zone}"
                    )
                    continue

        return pages_zones

    def extract_pages(self, pages: List[int]) -> List[Dict[str, Any]]:
        """
        Extracts the pages from the documents and returns them in a dictionary.
        Args:
            pages (List[int]): The pages to extract.
        Returns:
            documents (List[Dict[str, Any]]): The extracted pages.
        """
        document = [self.ocr_plu["pages"][page] for page in pages]

        return document
