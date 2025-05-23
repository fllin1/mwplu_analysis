from datetime import date
from pathlib import Path

from src.api import ocr_mistral
from src.config import (
    EXTERNAL_DATA_DIR,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
)
from src.prompt.txt_to_json import convert_prompts_txt_to_json


def main(
    city: str,
    date_creation_source_document: date.isoformat,
    name_city: str,
    name_document: str,
) -> None:
    """
    TODO : Detail the function
    """
    # Step 0: Setup prompts
    convert_prompts_txt_to_json()

    # Step 1: OCR
    external_path = (EXTERNAL_DATA_DIR / city / name_document).with_suffix(".pdf")
    raw_path = (RAW_DATA_DIR / city / name_document).with_suffix(".json")

    ocr_mistral(
        path_input=external_path,
        path_output=raw_path,
        date_creation_source_document=date_creation_source_document,
        name_city=name_city,
        name_document=name_document,
    )
