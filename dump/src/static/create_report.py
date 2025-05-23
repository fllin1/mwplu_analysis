# -*- coding: utf-8 -*-
"""PDF Generator for Structured JSON Data

This script converts structured JSON data into a PDF document.
It uses ReportLab to create the PDF and handles various formatting options.

Version: 1.2
Date: 2025-04-13
Author: Grey Panda
"""

import re
from pathlib import Path

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
from xml.sax import saxutils

from loguru import logger
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer


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


# --------------------------------------
# ----------MAIN FUNCTIONS--------------
# --------------------------------------


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
    json_data: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
    source_links: Dict[str, str],
) -> List[Flowable]:
    """
    Processes the JSON data into ReportLab Flowables, embedding source links.

    Returns:
        List[Flowable]: The list of ReportLab elements for the main content.
    """
    elements: List[Flowable] = []

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
                                    # Look up the link for the source
                                    doc_name = _parse_source_doc_name(source_string)
                                    link = (
                                        source_links.get(doc_name) if doc_name else None
                                    )

                                    if link:
                                        # Create hyperlink
                                        link_text = escape_html_in_text(
                                            source_string
                                        )  # Use original source string as link text
                                        elements.append(
                                            Paragraph(
                                                f'Source : <a href="{link}" color="blue">{link_text}</a>',
                                                styles["Source"],
                                            )
                                        )
                                    else:
                                        # Display plain text and log warning if doc_name was found but no link
                                        elements.append(
                                            Paragraph(
                                                f"Source : {escape_html_in_text(source_string)}",  # Display plain text
                                                styles["Source"],
                                            )
                                        )
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
                                            doc_name = _parse_source_doc_name(
                                                source_string
                                            )
                                            link = (
                                                source_links.get(doc_name)
                                                if doc_name
                                                else None
                                            )
                                            if link:
                                                link_text = escape_html_in_text(
                                                    source_string
                                                )
                                                elements.append(
                                                    Paragraph(
                                                        f'Source : <a href="{link}" color="blue">{link_text}</a>',
                                                        styles["Source"],
                                                    )
                                                )
                                            else:
                                                elements.append(
                                                    Paragraph(
                                                        f"Source : {escape_html_in_text(source_string)}",
                                                        styles["Source"],
                                                    )
                                                )
                                        elements.append(Spacer(1, 2))
                    elif isinstance(subsections, str):
                        # Direct content string under section (handle potential edge case)
                        main_content, source_string = extract_source(subsections)
                        elements.append(Paragraph(main_content, styles["Content"]))
                        if source_string:
                            doc_name = _parse_source_doc_name(source_string)
                            link = source_links.get(doc_name) if doc_name else None
                            if link:
                                link_text = escape_html_in_text(source_string)
                                elements.append(
                                    Paragraph(
                                        f'Source : <a href="{link}" color="blue">{link_text}</a>',
                                        styles["Source"],
                                    )
                                )
                            else:
                                elements.append(
                                    Paragraph(
                                        f"Source : {escape_html_in_text(source_string)}",
                                        styles["Source"],
                                    )
                                )
                        elements.append(Spacer(1, 3))
                    # Add handling for other potential structures if necessary

    return elements


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


def convert_json_to_pdf(
    json_data: Dict[str, Any],
    output_pdf: Union[str, Path],
    source_links: Dict[str, str],  # Added source_links, removed folder
    margin: float = 2.0,
    title_size: int = 16,
) -> None:
    """
    Converts structured JSON data into a PDF document using ReportLab,
    embedding web links for sources.

    Args:
        json_data (Dict[str, Any]): The structured data to convert.
        output_pdf (Union[str, Path]): Path to save the final generated PDF file.
        source_links (Dict[str, str]): Dictionary mapping base source document names to web links.
        margin (float, optional): Page margin in centimeters. Defaults to 2.0.
        title_size (int, optional): Base font size for the main title. Defaults to 16.
    """
    output_pdf_path = Path(output_pdf)  # Use output_pdf_path directly
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _create_styles(title_size)
    # Process data to get elements with embedded links
    assert isinstance(source_links, dict), (
        "source_links should be a dictionary mapping document names to URLs."
    )
    if source_links == {}:
        logger.warning("No source links provided. No hyperlinks will be created.")

    elements = _process_json_data(json_data, styles, source_links)  # Pass source_links

    # Removed temporary file logic

    try:
        doc = SimpleDocTemplate(
            str(output_pdf_path),  # Build directly to the final output path
            pagesize=A4,
            rightMargin=margin * cm,
            leftMargin=margin * cm,
            topMargin=margin * cm,
            bottomMargin=margin * cm,
        )

        # Build the final PDF safely
        _build_pdf_safe(doc, elements, styles, str(output_pdf_path))

    except Exception as e:
        logger.error(f"Failed during PDF generation process: {e}")
    # Removed finally block for temp file cleanup
