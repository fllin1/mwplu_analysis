"""Generator Module
This module provides functions to generate HTML reports from PLU JSON data.

Version: 1.0
Date: 2025-05-25
Author: Grey Panda
"""

from .html_generator import generate_html_report
from .pdf_generator import generate_pdf_report

__all__ = ["generate_html_report", "generate_pdf_report"]
