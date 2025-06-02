# -*- coding: utf-8 -*-
"""
This module contains functions to generate PDF and HTML reports from the given JSON file.

Version: 0.1.4
Date: 2025-05-26
Author: Grey Panda
"""

import html
import json
import re
from typing import Any, Dict, List, Optional
from functools import partial

# from PIL import Image # No longer needed for SVG
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.platypus.flowables import Flowable
from svglib.svglib import svg2rlg  # Re-added for SVG


def _draw_logo(canvas, logo_path: str, width_cm: float = 6.9) -> Optional[float]:
    """
    Draw the SVG logo centered at the top.
    Returns the y-coordinate below the logo for potential subsequent drawing, or None on failure.
    Assumes logo_path points to a valid SVG file.
    """
    drawing = svg2rlg(logo_path)
    target_width_pt = width_cm * cm

    # Handle cases where initial width or height might be zero to avoid ZeroDivisionError
    # and ensure aspect ratio is maintained if possible.
    if drawing.width == 0 and drawing.height != 0:  # Only height is defined, width is 0
        scale = target_width_pt / (
            drawing.height * (target_width_pt / (A4[1] * 0.1))
        )  # Heuristic for width if original is 0
    elif (
        drawing.height == 0 and drawing.width != 0
    ):  # Only width is defined, height is 0
        scale = target_width_pt / drawing.width
    elif drawing.width != 0 and drawing.height != 0:  # Both defined
        scale = target_width_pt / drawing.width
    else:
        return None

    scaled_width = drawing.width * scale
    scaled_height = drawing.height * scale

    drawing.width = scaled_width
    drawing.height = scaled_height
    drawing.scale(scale, scale)  # Ensure transform is applied correctly
    drawing.translate(0, 0)  # Ensure it's drawn from its origin

    x_pt = (A4[0] - drawing.width) / 2
    y_pt = A4[1] - drawing.height - 5.2 * cm  # 5.2cm from top edge to top of logo

    canvas.saveState()
    try:
        renderPDF.draw(drawing, canvas, x_pt, y_pt)
    finally:
        canvas.restoreState()

    return y_pt - 2 * cm


def _draw_page_logo(canvas, logo_path_tl: str, width_cm: float = 2.0):
    """
    Draw an SVG logo at the bottom-left of the canvas.
    Assumes logo_path_tl points to a valid SVG file.
    """
    if not logo_path_tl:
        return
    try:
        drawing_tl = svg2rlg(logo_path_tl)
        if not drawing_tl:
            return

        if drawing_tl.width == 0 or drawing_tl.height == 0:
            if drawing_tl.width == 0 and drawing_tl.height == 0:
                return

        target_width_pt = width_cm * cm

        if drawing_tl.width == 0 and drawing_tl.height != 0:
            scale_tl = target_width_pt / (
                drawing_tl.height * (target_width_pt / (A4[1] * 0.05))
            )  # Heuristic
        elif drawing_tl.height == 0 and drawing_tl.width != 0:
            scale_tl = target_width_pt / drawing_tl.width
        elif drawing_tl.width != 0 and drawing_tl.height != 0:
            scale_tl = target_width_pt / drawing_tl.width
        else:  # Both zero
            return

        scaled_width_tl = drawing_tl.width * scale_tl
        scaled_height_tl = drawing_tl.height * scale_tl

        if scaled_width_tl == 0 or scaled_height_tl == 0:
            if scaled_width_tl == 0 and scaled_height_tl == 0:
                return

        drawing_tl.width = scaled_width_tl
        drawing_tl.height = scaled_height_tl
        drawing_tl.scale(scale_tl, scale_tl)
        drawing_tl.translate(0, 0)

        x_pos_pt = 1.6 * cm
        y_pos_pt = 0.2 * cm  # Now from the bottom edge

        canvas.saveState()
        try:
            renderPDF.draw(drawing_tl, canvas, x_pos_pt, y_pos_pt)
        finally:
            canvas.restoreState()

    except FileNotFoundError:
        print(f"Error: Bottom-left SVG logo file not found at {logo_path_tl}")
    except Exception as e:
        print(
            f"Error processing or drawing bottom-left SVG logo from {logo_path_tl}: {e}"
        )


def _parse_json(json_path: str) -> Dict:
    """
    Parse the JSON file and return the data.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _add_references(story, reference_links: Optional[Dict[str, str]] = None) -> None:
    """
    Add the references page with legal mentions and company information.
    """
    if reference_links is None:
        reference_links = {}

    references_bookmark_name = "Références et Mentions Légales"

    class ReferencesBookmarkFlowable(Flowable):
        """
        A flowable that adds a bookmark for the references page.
        """

        def __init__(self, bookmark_name):
            super().__init__()
            self.bookmark_name = bookmark_name
            self.width = 0
            self.height = 0

        def wrap(self, availWidth, availHeight):
            return (0, 0)

        def draw(self):
            """
            Draw the references page bookmark.
            """
            self.canv.bookmarkPage(self.bookmark_name)
            self.canv.addOutlineEntry(self.bookmark_name, self.bookmark_name, 0)

    story.append(ReferencesBookmarkFlowable(references_bookmark_name))

    title_style = ParagraphStyle(
        name="RefTitle",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceBefore=24,
        spaceAfter=12,
        textColor=black,
    )
    section_style = ParagraphStyle(
        name="RefSection",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=16,
        spaceAfter=8,
        textColor=black,
    )
    content_style = ParagraphStyle(
        name="RefContent",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceBefore=4,
        spaceAfter=4,
        textColor=HexColor("#222222"),
    )
    company_style = ParagraphStyle(
        name="CompanyInfo",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceBefore=4,
        spaceAfter=4,
        textColor=HexColor("#444444"),
    )

    story.append(Paragraph("Références et Mentions Légales", title_style))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Références d'urbanisme", section_style))
    link = reference_links.get("source_plu_url", "-")
    story.append(
        Paragraph(
            (
                f'<a href="{link}">Lien vers les documents PLU complets</a>'
                if link != "-"
                else "Lien vers les documents PLU complets : -"
            ),
            content_style,
        )
    )

    link = reference_links.get("vocabulaire", "-")
    story.append(
        Paragraph(
            (
                f'<a href="{link}">Accéder au vocabulaire de l\'urbanisme</a>'
                if link != "-"
                else "Vocabulaire de l'urbanisme : -"
            ),
            content_style,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    story.append(
        Paragraph("Mentions légales et politique de confidentialité", section_style)
    )
    sections = [
        ("Politiques de vente", "politiques_vente"),
        ("Politique de confidentialité", "politique_confidentialite"),
        ("Conditions générales d'utilisation", "cgu"),
    ]
    for section_name, key in sections:
        link = reference_links.get(key, "-")
        story.append(
            Paragraph(
                (
                    f'<a href="{link}">Accéder à {section_name.lower()}</a>'
                    if link != "-"
                    else f"{section_name} : -"
                ),
                content_style,
            )
        )

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Informations Société", section_style))
    story.append(Paragraph("Société : MEWE PARTNERS SAS (MWP)", company_style))
    story.append(Paragraph("SIRET : 94134170300010", company_style))
    story.append(Paragraph("Dirigeants : Zakaria TOUATI, Rim ENNACIRI", company_style))


def _generate_outline(response: Dict[str, Any]) -> List:
    outline_story = []
    outline_title_style = ParagraphStyle(
        name="OutlineTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        spaceBefore=0,
        spaceAfter=16,
        textColor=black,
    )
    chapter_style = ParagraphStyle(
        name="OutlineChapter",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=8,
        spaceAfter=4,
        textColor=black,
    )
    section_style = ParagraphStyle(
        name="OutlineSection",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceBefore=2,
        spaceAfter=2,
        leftIndent=20,
        textColor=HexColor("#444444"),
    )

    outline_story.append(Paragraph("Sommaire", outline_title_style))
    for chapitre_key, chapitre_data in response.items():
        chapter_display_title = chapitre_key.replace("_", " ").title()
        chapter_bookmark_name = chapter_display_title
        outline_story.append(
            Paragraph(
                f'<a href="#{chapter_bookmark_name}">{chapter_display_title}</a>',
                chapter_style,
            )
        )
        for section_key in chapitre_data:
            section_match = re.search(r"(\d+)", section_key)
            if not section_match:
                continue
            section_number = int(section_match.group(1))
            section_display_title = _get_section_title(section_number)
            section_bookmark_name = re.sub(
                r"[^\w\s-]", "", section_display_title
            ).strip()
            outline_story.append(
                Paragraph(
                    f'<a href="#{section_bookmark_name}">{section_display_title}</a>',
                    section_style,
                )
            )

    references_title = "Références et Mentions Légales"
    references_bookmark_name = references_title
    outline_story.append(
        Paragraph(
            f'<a href="#{references_bookmark_name}">{references_title}</a>',
            chapter_style,
        )
    )
    return outline_story


def _add_section(
    story,
    title: str,
    content: Optional[str],
    level: int = 1,
    add_bookmark: bool = False,
    bookmark_name: Optional[str] = None,
) -> None:
    left_indent_h3 = 0.5 * cm
    styles = {
        1: ParagraphStyle(
            name="H1",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            spaceBefore=18,
            spaceAfter=8,
            textColor=black,
        ),
        2: ParagraphStyle(
            name="H2",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=14,
            spaceAfter=6,
            textColor=black,
        ),
        3: ParagraphStyle(
            name="H3",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=4,
            textColor=black,
            leftIndent=left_indent_h3,
        ),
        4: ParagraphStyle(
            name="H4",
            fontName="Helvetica-Oblique",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=2,
            textColor=black,
        ),
    }
    style = styles.get(level, styles[4])

    if add_bookmark and title:
        current_bookmark_name = bookmark_name if bookmark_name else title

        class BookmarkFlowable(Flowable):
            """
            A flowable that adds a bookmark for the section.
            """

            def __init__(self, bm_name, bm_level):
                super().__init__()
                self.bookmark_name = bm_name
                self.level = bm_level
                self.width = 0
                self.height = 0

            def wrap(self, availWidth, availHeight):
                return (0, 0)

            def draw(self):
                """
                Draw the section bookmark.
                """
                self.canv.bookmarkPage(self.bookmark_name)
                self.canv.addOutlineEntry(
                    self.bookmark_name, self.bookmark_name, self.level - 1
                )

        story.append(BookmarkFlowable(current_bookmark_name, level))

    story.append(Paragraph(title, style))
    if content:
        body_style = ParagraphStyle(
            name="Body",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            spaceBefore=0,
            spaceAfter=8,
            textColor=HexColor("#222222"),
        )
        story.append(Paragraph(content, body_style))


def _add_regles(story, regles: List[Dict[str, str]]) -> None:
    for regle in regles:
        contenu = html.escape(regle.get("contenu", ""))
        page_source = html.escape(regle.get("page_source", ""))
        text = contenu
        if page_source:
            text += f' <font size="9" color="#888888">({page_source})</font>'
        _add_section(story, "", text, level=4)


def _get_section_title(section_number: int) -> str:
    section_titles = {
        1: "1 - Constructions, usages et affectations des sols, activités et installations interdits",
        2: "2 - Constructions, usages et affectations des sols, activités et installations soumises à conditions particulières",
        3: "3 - Mixité fonctionnelle et sociale",
        4: "4 - Implantation et volumétrie des constructions et des installations",
        5: "5 - Qualité urbaine, architecturale, environnementale et paysagère",
        6: "6 - Traitement environnemental et paysager des espaces non bâtis, des constructions et de leurs abords",
        7: "7 - Stationnement",
        8: "8 - Desserte par les voies publiques et privées",
        9: "9 - Desserte par les réseaux",
        10: "10 - Energie et performances énergétiques",
    }
    return section_titles.get(section_number, f"{section_number} - Section")


def _add_chapitre(story, chapitre: Dict[str, Any], chapitre_key: str) -> None:
    chapter_display_title = chapitre_key.replace("_", " ").title()
    chapter_bookmark_name = chapter_display_title
    _add_section(
        story,
        chapter_display_title,
        None,
        level=1,
        add_bookmark=True,
        bookmark_name=chapter_bookmark_name,
    )

    for section_key, sections_data in chapitre.items():
        section_match = re.search(r"(\d+)", section_key)
        if section_match:
            section_number = int(section_match.group(1))
            section_display_title = _get_section_title(section_number)
            section_bookmark_name = re.sub(
                r"[^\w\s-]", "", section_display_title
            ).strip()

            class SectionBookmarkFlowable(Flowable):
                """
                A flowable that adds a bookmark for the section.
                """

                def __init__(self, bm_name):
                    super().__init__()
                    self.bookmark_name = bm_name
                    self.width = 0
                    self.height = 0

                def wrap(self, availWidth, availHeight):
                    return (0, 0)

                def draw(self):
                    """
                    Draw the section bookmark.
                    """
                    self.canv.bookmarkPage(self.bookmark_name)
                    self.canv.addOutlineEntry(self.bookmark_name, self.bookmark_name, 1)

            story.append(SectionBookmarkFlowable(section_bookmark_name))
            _add_section(
                story, section_display_title, None, level=2, add_bookmark=False
            )

            if section_number == 10:
                if len(sections_data) > 0:
                    _add_regles(story, sections_data[0].get("regles", []))
                else:
                    _add_section(story, "Aucune règle", None, level=4)
            else:
                for sous_section in sections_data:
                    titre_sous_section = f"{sous_section.get('sous_section', '')} - {sous_section.get('titre', '')}"
                    if titre_sous_section.strip() != " - ":
                        _add_section(
                            story, titre_sous_section, None, level=3, add_bookmark=False
                        )
                        _add_regles(story, sous_section.get("regles", []))
        else:
            fallback_section_title = section_key.replace("_", " ").title()
            _add_section(
                story,
                fallback_section_title,
                None,
                level=2,
                add_bookmark=True,
                bookmark_name=fallback_section_title,
            )
            for sous_section in sections_data:
                titre = f"{sous_section.get('sous_section', '')} - {sous_section.get('titre', '')}"
                _add_section(story, titre, None, level=3)
                _add_regles(story, sous_section.get("regles", []))


def generate_pdf_report(
    json_path: str,
    logo_path: str,  # Now expects an SVG path
    references: Optional[Dict[str, str]],
    output_path: str,
    page_logo_path: Optional[str] = None,  # Now expects an SVG path
) -> None:
    """
    Generate a sober, elegant, minimalist PDF report from the given JSON file, using SVG logos.

    Args:
        json_path (str): The path to the JSON file.
        logo_path (str): The path to the main SVG logo (centered on first page).
        references (Optional[Dict[str, str]]): Dictionary of reference links.
        output_path (str): The path to save the PDF report.
        page_logo_path (Optional[str]): Path to the SVG logo for top-left of each page.
                                            If None, no top-left logo is drawn.
    """
    data = _parse_json(json_path)
    response = data.get("response", {})
    metadata = data.get("metadata", {})

    story = []
    story.append(Spacer(1, 12 * cm))
    story.append(
        Paragraph(
            metadata.get("name_city", "").upper(),
            ParagraphStyle(
                name="City",
                fontName="Helvetica-Bold",
                fontSize=22,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=black,
            ),
        )
    )
    story.append(
        Paragraph(
            metadata.get("name_zoning", ""),
            ParagraphStyle(
                name="Zoning",
                fontName="Helvetica",
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=16,
                textColor=black,
            ),
        )
    )
    story.append(
        Paragraph(
            f"Zone {metadata.get('name_zone', '-')}",
            ParagraphStyle(
                name="Zone",
                fontName="Helvetica",
                fontSize=16,
                alignment=TA_CENTER,
                spaceAfter=32,
                textColor=HexColor("#222222"),
            ),
        )
    )
    story.append(Spacer(1, 4 * cm))
    story.append(
        Paragraph(
            "<a href='https://mwplu.com'>mwplu.com</a>",
            ParagraphStyle(
                name="Website",
                fontName="Helvetica",
                fontSize=11,
                alignment=TA_CENTER,
                spaceAfter=6,
                textColor=HexColor("#444444"),
            ),
        )
    )
    story.append(
        Paragraph(
            "<a href='mailto:contact@mwplu.com'>contact@mwplu.com</a>",
            ParagraphStyle(
                name="Email",
                fontName="Helvetica",
                fontSize=11,
                alignment=TA_CENTER,
                spaceAfter=6,
                textColor=HexColor("#444444"),
            ),
        )
    )
    story.append(Spacer(1, 2 * cm))
    story.append(PageBreak())

    toc_bookmark_name = "sommaire"

    class TOCBookmarkFlowable(Flowable):
        """
        A flowable that adds a bookmark for the TOC.
        """

        def __init__(self, bookmark_name):
            super().__init__()
            self.bookmark_name = bookmark_name
            self.width = 0
            self.height = 0

        def wrap(self, availWidth, availHeight):
            return (0, 0)

        def draw(self):
            """
            Draw the TOC bookmark.
            """
            self.canv.bookmarkPage(self.bookmark_name)
            self.canv.addOutlineEntry(
                self.bookmark_name.title(), self.bookmark_name, 0, 0
            )

    story.append(TOCBookmarkFlowable(toc_bookmark_name))
    outline_content = _generate_outline(response)
    story.extend(outline_content)
    story.append(PageBreak())

    for chapitre_key, chapitre_content in response.items():
        _add_chapitre(story, chapitre_content, chapitre_key)
        story.append(PageBreak())

    _add_references(story, references)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.9 * cm,
        bottomMargin=1.6 * cm,
        title=metadata.get("name_zone", "Synthèse PLU"),
        author="SIFT - MEWE",
    )

    # Wrapper functions for page events to pass arguments
    def on_first_page_handler(canvas, doc_obj, main_logo_path_fp, metadata_fp):
        # Draw main centered logo (original functionality)
        if main_logo_path_fp:
            _draw_logo(canvas, main_logo_path_fp)

        # Set document metadata (already set by SimpleDocTemplate, but can be set here too)
        canvas.setTitle(metadata_fp.get("name_zone", "Synthèse PLU"))
        canvas.setAuthor("SIFT - MEWE")

    def on_later_pages_handler(
        canvas, doc_obj, page_logo_path_lp, toc_bookmark_name_lp
    ):
        # Draw top-left logo
        if page_logo_path_lp:
            _draw_page_logo(canvas, page_logo_path_lp)

        # Footer "▲ Sommaire" link
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#666666"))
        text = "▲ Sommaire"
        text_width = canvas.stringWidth(text, "Helvetica", 8)

        # Position near the right margin using A4 width and doc's right margin
        x_pos = (
            A4[0] - doc_obj.rightMargin - text_width - (0.2 * cm)
        )  # Small offset from margin
        y_pos = 0.8 * cm
        canvas.drawString(x_pos, y_pos, text)

        text_height_pts = 8
        rect_coords = (x_pos, y_pos, x_pos + text_width, y_pos + text_height_pts)
        canvas.linkRect("", toc_bookmark_name_lp, rect_coords, relative=0)

    # Bind arguments to the handlers
    bound_on_first_page = partial(
        on_first_page_handler,
        main_logo_path_fp=logo_path,
        metadata_fp=metadata,
    )
    bound_on_later_pages = partial(
        on_later_pages_handler,
        page_logo_path_lp=page_logo_path,
        toc_bookmark_name_lp=toc_bookmark_name,
    )

    doc.build(story, onFirstPage=bound_on_first_page, onLaterPages=bound_on_later_pages)
