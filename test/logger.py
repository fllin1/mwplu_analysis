#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Logger configuration for the application."""

import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    level="TRACE",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# Configure to show exceptions
logger.enable("src")
