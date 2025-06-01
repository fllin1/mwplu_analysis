# -*- coding: utf-8 -*-
"""Function to strandardize Mistral OCR output.

Expected format for further analysis.
./references/api/ocr_output.json

Model version: mistral-ocr-2503-completion

Version: 1.0
Date: 2025-05-21
Author: Grey Panda
"""


def standardize_ocr_output(
    ocr_response: dict,
    date_creation_source_document: str,
    name_city: str,
    name_zoning: str,
    name_document: str,
    table_name: str = "ocr_response",
) -> dict:
    """
    Standardize the OCR output from Mistral API.

    Args:
        ocr_response (dict): The OCR response from Mistral API.
        date_creation_source_document (str): The date of creation of the source document.
        city (str): The city associated with the document.
        zoning (str): The zoning associated with the document.
        name_bucket (str): The name of the bucket where images are stored.
            Defaults to "ocr_images".

    Returns:
        dict: Formatted OCR output.
    """
    formatted_output = {
        "pages": [
            {
                "number_page": page["index"] + 1,
                "text": page["markdown"].replace("img-", "img_"),
                "images": [
                    {
                        "name_img": image["id"].replace("img-", "img_"),
                        "top_left_x": image["top_left_x"],  # additional field
                        "top_left_y": image["top_left_y"],  # additional field
                        "bottom_right_x": image["bottom_right_x"],  # additional field
                        "bottom_right_y": image["bottom_right_y"],  # additional field
                        "image_base64": image["image_base64"].split(",")[1],
                    }
                    for image in page["images"]
                ],
                "dimensions": page["dimensions"],  # additional field
            }
            for page in ocr_response["pages"]
        ],
        "name_model": ocr_response["model"],
        "metadata": {
            "type_response": table_name,
            "name_city": name_city,
            "name_zoning": (
                name_zoning.replace("_", " ").title()
                if name_zoning != "None"
                else name_document
            ),
            "name_zone": name_document if name_zoning != "None" else name_document,
            "name_plu": name_document,
            "date_creation_source_document": date_creation_source_document,
            "number_total_page": ocr_response["usage_info"]["pages_processed"],
        },
    }

    return formatted_output
