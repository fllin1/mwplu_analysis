"""
Logger module for saving Gemini model responses to JSON files.
"""

import json
import logging
from datetime import datetime

from src.config import LOGS_DIR

# Logger configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def save_gemini_response(response: dict, model_name: str, operation: str) -> None:
    """
    Save the Gemini model response to a JSON file.

    Args:
        response (dict): The model response to save
        model_name (str): Name of the model used
        operation (str): Type of operation performed
    """
    LOGS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gemini_{model_name}_{operation}_{timestamp}.json"
    filepath = LOGS_DIR / filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        logger.info("Gemini response saved to %s", filepath)

    except TypeError as e:
        logger.error("Error saving Gemini response: %s", e)
