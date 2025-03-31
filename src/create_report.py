# -*- coding: utf-8 -*-
"""PDF Generator for Structured JSON Data

This script converts structured JSON data into a PDF document.
It uses ReportLab to create the PDF and handles various formatting options.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple
from xml.sax import saxutils  # Import correct module for XML escaping

import typer
import yaml
from loguru import logger
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from src.config import PROCESSED_DATA_DIR, PROJ_ROOT

app = typer.Typer(pretty_exceptions_enable=False)

# Loading the tree data structure
TREE_PATH: Path = PROJ_ROOT / Path("config/plu_tree.yaml")
tree: Dict[str, Any] = yaml.safe_load(TREE_PATH.read_text(encoding="utf-8"))


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


def convert_json_to_pdf(
    json_data: Dict[str, Any],
    output_pdf: str,
    margin: float,
    title_size: int,
) -> None:
    """
    Convert structured JSON data into a PDF document.
    Args:
        json_data (Dict[str, Any]): JSON data to convert
        output_pdf (str): Output PDF file path
        margin (float): Margin size in centimeters
        title_size (int): Font size for the titles
    """
    # Creation du document PDF
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=margin * cm,
        leftMargin=margin * cm,
        topMargin=margin * cm,
        bottomMargin=margin * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=title_size,
        spaceAfter=6,
        fontName="Helvetica-Bold",
        textColor=colors.darkblue,  # Color dark blue for the main title
    )
    chapter_style = ParagraphStyle(
        "Chapter",
        parent=styles["Heading2"],
        fontSize=title_size - 2,
        spaceAfter=2,
        fontName="Helvetica-Bold",
        textColor=colors.navy,  # Color navy for the chapters
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading3"],
        fontSize=title_size - 4,
        spaceAfter=2,
        leftIndent=8,
        fontName="Helvetica-Bold",
        textColor=colors.blue,  # Color blue for the sections
    )
    subsection_style = ParagraphStyle(
        "Subsection",
        parent=styles["Heading4"],
        fontSize=title_size - 5,
        spaceAfter=6,
        leftIndent=16,
        fontName="Helvetica-Bold",
        textColor=colors.royalblue,  # Color royal blue for the subsections
    )
    content_style = ParagraphStyle(
        "Content",
        parent=styles["Normal"],
        fontSize=title_size - 6,
        spaceAfter=4,
        leftIndent=24,
    )
    source_style = ParagraphStyle(
        "Source",
        parent=styles["Normal"],
        fontSize=title_size - 7,
        spaceAfter=6,
        leftIndent=32,
        textColor=colors.gray,  # Color gray for the source
    )

    elements = []

    # TITRE PRINCIPAL
    for main_title, chapters in json_data.items():
        elements.append(Paragraph(escape_html_in_text(main_title), title_style))
        elements.append(Spacer(1, 12))

        # CHAPITRES
        for chapter_title, sections in chapters.items():
            elements.append(
                Paragraph(escape_html_in_text(chapter_title), chapter_style)
            )
            elements.append(Spacer(1, 8))

            # SECTIONS
            for section_dict in sections:
                for section_title, subsections in section_dict.items():
                    elements.append(
                        Paragraph(escape_html_in_text(section_title), section_style)
                    )
                    elements.append(Spacer(1, 6))

                    # SOUS-SECTIONS ou CONTENU
                    if isinstance(subsections, list):
                        # Handling the case where subsections are a list (e.g., Section 10)
                        if all(isinstance(item, str) for item in subsections):
                            for content in subsections:
                                main_content, source = extract_source(content)
                                elements.append(Paragraph(main_content, content_style))
                                if source:
                                    elements.append(
                                        Paragraph(f"Source: {source}", source_style)
                                    )
                                elements.append(Spacer(1, 3))
                        else:
                            # Handling the case where subsections are a list of dictionaries
                            for subsection_dict in subsections:
                                for (
                                    subsection_title,
                                    contents,
                                ) in subsection_dict.items():
                                    elements.append(
                                        Paragraph(
                                            escape_html_in_text(subsection_title),
                                            subsection_style,
                                        )
                                    )
                                    elements.append(Spacer(1, 4))

                                    # CONTENU
                                    for content in contents:
                                        main_content, source = extract_source(content)
                                        elements.append(
                                            Paragraph(main_content, content_style)
                                        )
                                        if source:
                                            elements.append(
                                                Paragraph(
                                                    f"Source: {source}", source_style
                                                )
                                            )
                                        elements.append(Spacer(1, 2))

    try:
        doc.build(elements)
    except Exception as e:
        logger.error(f"Error while generating the pdf: {str(e)}")
        new_elements = []
        for element in elements:
            if isinstance(element, Paragraph):
                try:
                    # Attempt to extract the text and style
                    text = element.text
                    style = element.style
                    # Clean in case of an issue with the text
                    cleaned_text = re.sub(r"<[^>]+>", "", text)  # Remove HTML tags
                    new_elements.append(Paragraph(cleaned_text, style))
                except Exception:
                    # If there's an issue with the text, add a placeholder
                    new_elements.append(
                        Paragraph("Cannot display text", styles["Normal"])
                    )
            else:
                new_elements.append(element)

        # New attempt to build the document with simplified elements
        try:
            doc.build(new_elements)
            logger.info(f"Document generated with simplications {output_pdf}")
        except Exception as e2:
            logger.error(f"Failed attempt to generate: {str(e2)}")


@app.command()
def main(
    data_dir: Path = typer.Option(
        PROCESSED_DATA_DIR, "--dir", "-d", help="Directory for data"
    ),
    folder: str = typer.Option("Grenoble", "--folder", "-f", help="City folder"),
    margin: float = typer.Option(1.1, "--margin", "-m", help="Marge in cm"),
    title_size: int = typer.Option(16, "--title-size", "-t", help="Police size"),
):
    """
    Convert JSON files to PDF for a specific folder.
    Args:
        data_dir (Path): Directory containing the JSON files
        folder (str): Folder name to process
        margin (float): Margin size in cm
        title_size (int): Font size for titles

    Example:
        python create_report.py --folder Grenoble
    """
    for zone_type, zones in tree[folder]["documents_par_zone"].items():
        for zone in zones:
            # Files
            input_file: Path = (
                data_dir / Path(folder) / Path(zone_type) / Path(zone)
            ).with_suffix(".json")
            if not input_file.exists():
                logger.info(f"Fichier inexistant: {input_file.relative_to(PROJ_ROOT)}")
                continue

            output_dir = data_dir / Path(folder) / Path("pdf") / Path(zone_type)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file: Path = (output_dir / Path(f"{zone}_recap")).with_suffix(".pdf")

            # Charger les données JSON
            try:
                with open(input_file, "r", encoding="utf-8") as file:
                    content = file.read()
                    data = json.loads(content)["parsed"]

                # Appeler la fonction de conversion
                convert_json_to_pdf(
                    json_data=data,
                    output_pdf=str(output_file),
                    margin=margin,
                    title_size=title_size,
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la conversion de {input_file.name}: {str(e)}"
                )


if __name__ == "__main__":
    app()
