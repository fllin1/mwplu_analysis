# -*- coding: utf-8 -*-
"""PDF Generator for Structured JSON Data

This script converts structured JSON data into a PDF document.
It uses ReportLab to create the PDF and handles various formatting options.

Version: 1.1
Date: 2025-04-09
Author: Grey Panda
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from xml.sax import saxutils

from loguru import logger
from pypdf import PdfMerger  # Removed PdfReader as it's not used in the merging logic
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer

# Removed AnchorFlowable as we are not using internal anchors for annexes now
# from reportlab.platypus.flowables import AnchorFlowable
from src.config import INTERIM_DATA_DIR


def escape_html_in_text(text: str) -> str:
    """
    Escape the special HTML characters in a string to prevent issues with ReportLab
    when generating PDFs.
    Args:
        text (str): Text to escape
    Returns:
        str: Escaped text
    """
    if not isinstance(text, str):
        return str(text)

    return saxutils.escape(text)


def extract_source(content: str) -> Tuple[str, str]:
    """
    Extract the main content and the source from a string.
    Args:
        content (str): Content string potentially containing a source
    Returns:
        Tuple[str, str]: A tuple containing the main content and the source
    """
    escaped_content = escape_html_in_text(content)

    source_pattern = r"\(Source: ([^)]+)\)$"
    match = re.search(source_pattern, escaped_content)

    if match:
        source = match.group(1).strip()
        main_content = escaped_content[: match.start()].strip()
        return main_content, source

    return escaped_content, ""


# --------------------------
# ----------ANNEXE----------
# --------------------------


def _parse_source_doc_name(source_string: str) -> Optional[str]:
    """Parses the base document name from the source string."""
    # Case 1: "Document Name, Page X"
    match_page = re.match(r"(.*?),\s*Page(?:s)?\s*[\d\-–, ]+", source_string)
    if match_page:
        return match_page.group(1).strip()

    # Case 2: "Règlement zone X" (or similar patterns without "Page")
    # This is a bit more ambiguous, assume the whole string is the doc name if no page found
    # We might need more specific patterns if sources vary widely
    # For now, let's assume if "Page" isn't present, the whole string is the key part
    # Example: "Règlement zone A" -> "Règlement zone A"
    # Example: "Règles communes" -> "Règles communes"
    # We will format this into a filename later in _get_source_pdf_path
    return source_string.strip()


def _format_doc_name_to_filename(doc_name: str) -> str:
    """Formats the parsed document name into a PDF filename."""
    # Specific case: "Règles communes" -> "regles_communes.pdf"
    if doc_name.lower() == "règles communes":
        return "regles_communes.pdf"

    # General case: "Zone X" or "Règlement zone X" -> "Zone_X.pdf"
    # Try to extract "Zone X" part
    zone_match = re.search(r"(zone\s+[A-Z0-9]+)", doc_name, re.IGNORECASE)
    if zone_match:
        zone_part = zone_match.group(1).strip()
        # Replace space with underscore and ensure correct casing (e.g., Zone_A)
        formatted_zone = zone_part.replace(" ", "_").title().replace("zone", "Zone")
        return f"{formatted_zone}.pdf"

    # Fallback: Simple formatting for other cases
    filename_base = re.sub(r"\W+", "_", doc_name.lower())
    return f"{filename_base}.pdf"


# Removed _get_source_pdf_path as its logic is integrated into _append_annexes
# Removed generate_anchor_name as we are not using anchors for annexes anymore


# -------------------------------------
# ----------MAIN FUNCTION--------------
# -------------------------------------


def _create_styles(base_title_size: int) -> Dict[str, ParagraphStyle]:
    """Creates the paragraph styles for the PDF document."""
    styles = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=base_title_size,
            spaceAfter=6,
            fontName="Helvetica-Bold",
            textColor=colors.darkblue,
        ),
        "Chapter": ParagraphStyle(
            "Chapter",
            parent=styles["Heading2"],
            fontSize=base_title_size - 2,
            spaceAfter=2,
            fontName="Helvetica-Bold",
            textColor=colors.navy,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=styles["Heading3"],
            fontSize=base_title_size - 4,
            spaceAfter=2,
            leftIndent=8,
            fontName="Helvetica-Bold",
            textColor=colors.blue,
        ),
        "Subsection": ParagraphStyle(
            "Subsection",
            parent=styles["Heading4"],
            fontSize=base_title_size - 5,
            spaceAfter=6,
            leftIndent=16,
            fontName="Helvetica-Bold",
            textColor=colors.royalblue,
        ),
        "Content": ParagraphStyle(
            "Content",
            parent=styles["Normal"],
            fontSize=base_title_size - 6,
            spaceAfter=4,
            leftIndent=24,
        ),
        "Source": ParagraphStyle(
            "Source",
            parent=styles["Normal"],
            fontSize=base_title_size - 7,
            spaceAfter=6,
            leftIndent=32,
            textColor=colors.gray,
        ),
        "Normal": styles["Normal"],  # Include normal style for fallback
    }


def _process_json_data(
    json_data: Dict[str, Any], styles: Dict[str, ParagraphStyle]
) -> Tuple[List[Flowable], Set[str]]:
    """
    Processes the JSON data into ReportLab Flowables and extracts unique source doc names.

    Returns:
        Tuple containing:
        - List[Flowable]: The list of ReportLab elements for the main content.
        - Set[str]: A set of unique base document names found in sources.
    """
    elements: List[Flowable] = []
    unique_source_doc_names: Set[str] = set()

    for main_title, chapters in json_data.items():
        elements.append(Paragraph(escape_html_in_text(main_title), styles["Title"]))
        elements.append(Spacer(1, 12))

        for chapter_title, sections in chapters.items():
            elements.append(
                Paragraph(escape_html_in_text(chapter_title), styles["Chapter"])
            )
            elements.append(Spacer(1, 8))

            for section_dict in sections:
                for section_title, subsections in section_dict.items():
                    elements.append(
                        Paragraph(escape_html_in_text(section_title), styles["Section"])
                    )
                    elements.append(Spacer(1, 6))

                    if isinstance(subsections, list):
                        if all(isinstance(item, str) for item in subsections):
                            # Direct content under section
                            for content in subsections:
                                main_content, source_string = extract_source(content)
                                elements.append(
                                    Paragraph(main_content, styles["Content"])
                                )
                                if source_string:
                                    # Remove hyperlink, just display source text
                                    elements.append(
                                        Paragraph(
                                            f"Source : {escape_html_in_text(source_string)}",
                                            styles["Source"],
                                        )
                                    )
                                    # Extract and store unique base document name
                                    doc_name = _parse_source_doc_name(source_string)
                                    if doc_name:
                                        unique_source_doc_names.add(doc_name)
                                elements.append(Spacer(1, 3))
                        else:
                            # List of subsections
                            for subsection_dict in subsections:
                                for (
                                    subsection_title,
                                    contents,
                                ) in subsection_dict.items():
                                    elements.append(
                                        Paragraph(
                                            escape_html_in_text(subsection_title),
                                            styles["Subsection"],
                                        )
                                    )
                                    elements.append(Spacer(1, 4))
                                    for content in contents:
                                        main_content, source_string = extract_source(
                                            content
                                        )
                                        elements.append(
                                            Paragraph(main_content, styles["Content"])
                                        )
                                        if source_string:
                                            elements.append(
                                                Paragraph(
                                                    f"Source : {escape_html_in_text(source_string)}",
                                                    styles["Source"],
                                                )
                                            )
                                            doc_name = _parse_source_doc_name(
                                                source_string
                                            )
                                            if doc_name:
                                                unique_source_doc_names.add(doc_name)
                                        elements.append(Spacer(1, 2))
                    elif isinstance(subsections, str):
                        # Direct content string under section (handle potential edge case)
                        main_content, source_string = extract_source(subsections)
                        elements.append(Paragraph(main_content, styles["Content"]))
                        if source_string:
                            elements.append(
                                Paragraph(
                                    f"Source : {escape_html_in_text(source_string)}",
                                    styles["Source"],
                                )
                            )
                            doc_name = _parse_source_doc_name(source_string)
                            if doc_name:
                                unique_source_doc_names.add(doc_name)
                        elements.append(Spacer(1, 3))
                    # Add handling for other potential structures if necessary

    return elements, unique_source_doc_names


def _build_pdf_safe(
    doc: SimpleDocTemplate,
    elements: List[Flowable],
    styles: Dict[str, ParagraphStyle],
    output_pdf: str,
) -> None:
    """Attempts to build the PDF, with a fallback for encoding errors."""
    try:
        doc.build(elements)
        logger.success(f"Document generated: {output_pdf}")
    except Exception as e:
        logger.error(f"Error during initial PDF build: {str(e)}")
        logger.info("Attempting to build PDF with simplified elements...")
        simplified_elements = []
        for element in elements:
            if isinstance(element, Paragraph):
                try:
                    # Basic cleaning: remove HTML-like tags that might cause issues
                    cleaned_text = re.sub(r"<[^>]+>", "", element.text)
                    simplified_elements.append(Paragraph(cleaned_text, element.style))
                except Exception as style_error:
                    logger.warning(
                        f"Could not process paragraph, using fallback: {style_error}"
                    )
                    simplified_elements.append(
                        Paragraph("Error: Could not display content", styles["Normal"])
                    )
            else:
                simplified_elements.append(element)

        try:
            doc.build(simplified_elements)
            logger.success(f"Document generated with simplifications: {output_pdf}")
        except Exception as e2:
            logger.error(f"Failed to build simplified PDF: {str(e2)}")


def _append_annexes(
    main_content_pdf_path: str,
    final_output_path: Path,
    source_doc_names: Set[str],
    folder: str,
) -> None:
    """
    Appends source PDFs (annexes) to the main generated PDF content.

    Args:
        main_content_pdf_path (str): Path to the temporary PDF with main content.
        final_output_path (Path): Path to save the final merged PDF.
        source_doc_names (Set[str]): Set of unique base document names for annexes.
        folder (str): The subfolder within INTERIM_DATA_DIR containing source PDFs.
    """
    merger = PdfMerger()
    try:
        # Append the main document first
        if (
            os.path.exists(main_content_pdf_path)
            and os.path.getsize(main_content_pdf_path) > 0
        ):
            merger.append(main_content_pdf_path)
            logger.debug(f"Appended main content PDF: {main_content_pdf_path}")
        else:
            logger.error(
                f"Main content PDF is missing or empty: {main_content_pdf_path}"
            )
            # Decide if we should proceed without main content or raise error
            # For now, let's log error and continue to append annexes if any

        # Append each source document found
        appended_annex_count = 0
        sorted_doc_names = sorted(list(source_doc_names))  # Sort for consistent order

        for doc_name in sorted_doc_names:
            filename = _format_doc_name_to_filename(doc_name)
            source_pdf_path = INTERIM_DATA_DIR / folder / filename

            if source_pdf_path.exists():
                try:
                    merger.append(str(source_pdf_path))
                    logger.info(f"Appended annex: {source_pdf_path}")
                    appended_annex_count += 1
                except Exception as append_error:
                    logger.error(
                        f"Failed to append annex {source_pdf_path}: {append_error}"
                    )
            else:
                logger.warning(f"Annex PDF not found, skipping: {source_pdf_path}")

        # Write the final merged PDF
        if appended_annex_count > 0 or (
            os.path.exists(main_content_pdf_path)
            and os.path.getsize(main_content_pdf_path) > 0
        ):
            with open(final_output_path, "wb") as f_out:
                merger.write(f_out)
            logger.success(
                f"Final PDF with {appended_annex_count} annex(es) saved to: {final_output_path}"
            )
        else:
            logger.error(
                "No main content or annexes were appended. Final PDF not created."
            )

    except Exception as merge_error:
        logger.error(f"Error during PDF merging process: {merge_error}")
    finally:
        merger.close()
        logger.debug("PdfMerger closed.")


def convert_json_to_pdf(
    json_data: Dict[str, Any],
    output_pdf: Union[str, Path],
    folder: str,  # New argument for the source PDF subfolder
    margin: float = 2.0,
    title_size: int = 16,
) -> None:
    """
    Converts structured JSON data into a PDF document using ReportLab,
    then appends source PDFs found in the specified folder as annexes.

    Args:
        json_data (Dict[str, Any]): The structured data to convert.
        output_pdf (Union[str, Path]): Path to save the final generated PDF file.
        folder (str): The subfolder within INTERIM_DATA_DIR containing source PDFs.
        margin (float, optional): Page margin in centimeters. Defaults to 2.0.
        title_size (int, optional): Base font size for the main title. Defaults to 16.
    """
    final_output_path = Path(output_pdf)
    final_output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _create_styles(title_size)
    # Process data to get elements and the names of source documents needed for annexes
    elements, unique_source_doc_names = _process_json_data(json_data, styles)

    # --- Generate Main Content PDF (Temporarily) ---
    # Create a temporary file for the main content generated by ReportLab
    temp_fd, temp_main_pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(temp_fd)  # Close the file descriptor, SimpleDocTemplate will open the path

    try:
        doc = SimpleDocTemplate(
            temp_main_pdf_path,  # Build the main content to the temporary file
            pagesize=A4,
            rightMargin=margin * cm,
            leftMargin=margin * cm,
            topMargin=margin * cm,
            bottomMargin=margin * cm,
        )

        # Build the main part (without annexes) safely
        _build_pdf_safe(doc, elements, styles, temp_main_pdf_path)

        # --- Append Annexes ---
        # Merge the generated main content with the source PDFs
        _append_annexes(
            temp_main_pdf_path, final_output_path, unique_source_doc_names, folder
        )

    except Exception as e:
        logger.error(f"Failed during PDF generation or merging process: {e}")
    finally:
        # --- Clean up temporary file ---
        try:
            os.remove(temp_main_pdf_path)
            logger.debug(f"Removed temporary file: {temp_main_pdf_path}")
        except OSError as e:
            logger.error(f"Error removing temporary file {temp_main_pdf_path}: {e}")
