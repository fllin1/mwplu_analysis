# -*- coding: utf-8 -*-
"""Project configuration.

This module contains the configuration settings for the project.

Version: 1.0
Date: 2025-03-31
Author: Florent Lin
"""

from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJ_ROOT / "data"
BACKUP_DIR = PROJ_ROOT / "backup"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

REFERENCES_DIR = PROJ_ROOT / "references"
CONFIG_DIR = PROJ_ROOT / "config"
LOGS_DIR = PROJ_ROOT / "logs"

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
