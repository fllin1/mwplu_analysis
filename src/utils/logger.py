"""Logger module for saving Gemini model responses to JSON files.

This module is used to save the raw Gemini model responses to JSON files.

Version: 1.0.0
Author: Greypanda
Date: 2025-05-25
"""

import logging
from datetime import datetime
from typing import Any

from src.config import LOGS_DIR

# NOTE : Logger configuration to retrieve API calls and responses
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )
logger = logging.getLogger(__name__)


def save_gemini_response(response: Any, model_name: str, operation: str) -> None:
    """
    Save the raw Gemini model response to a log file.

    Args:
        response (Any): The raw model response to save
        model_name (str): Name of the model used
        operation (str): Type of operation performed
        folder (str): Folder to save the response
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date = datetime.now().strftime("%Y%m%d")
    filename = f"gemini_{model_name}_{operation}_{timestamp}.log"
    filepath = LOGS_DIR / operation / date / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            # Converts the response to a string if it's not already the case
            if isinstance(response, str):
                f.write(response)
            else:
                # For Gemini Response or other types
                f.write(str(response))

        logger.info("Gemini raw response saved to %s", filepath)

    except Exception as e:
        logger.error("Error saving Gemini response: %s", e)
        # Optional: try to save at least something
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Error occurred while saving response: {e}\n")
                f.write(f"Response type: {type(response)}\n")
        except Exception:
            pass
