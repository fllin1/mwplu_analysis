# -*- coding: utf-8 -*-
"""HTML Generator Module
This module provides functions to generate HTML reports from PLU JSON data.

Version: 1.0
Date: 2025-05-25
Author: Grey Panda
"""

import html
import re
from typing import Any, Dict, List


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)


def _get_section_title(section_number: int) -> str:
    """Get the full title for a section number."""
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


def generate_html_report(json_data: Dict[str, Any]) -> str:
    """
    Generate an HTML report from PLU JSON data.

    Args:
        json_data: The JSON data containing response and metadata

    Returns:
        str: The generated HTML content
    """
    response = json_data.get("response", {})

    # Start HTML document
    html_parts = [
        '<div class="container">',
    ]

    # Add table of contents
    html_parts.append('<nav class="toc">')
    html_parts.append("<h2>Sommaire</h2>")
    html_parts.append("<ul>")

    for chapitre_key, chapitre_data in response.items():
        chapter_title = chapitre_key.replace("_", " ").title()
        chapter_id = chapitre_key
        html_parts.append(f'<li><a href="#{chapter_id}">{chapter_title}</a>')

        if chapitre_data:
            html_parts.append("<ul>")
            for section_key in chapitre_data:
                section_match = re.search(r"(\d+)", section_key)
                if section_match:
                    section_number = int(section_match.group(1))
                    section_title = _get_section_title(section_number)
                    section_id = f"section_{section_number}"
                    html_parts.append(
                        f'<li><a href="#{section_id}">{section_title}</a></li>'
                    )
            html_parts.append("</ul>")
        html_parts.append("</li>")

    html_parts.append("</ul>")
    html_parts.append("</nav>")

    # Add main content
    html_parts.append("<main>")

    for chapitre_key, chapitre_data in response.items():
        chapter_title = chapitre_key.replace("_", " ").title()
        chapter_id = chapitre_key

        html_parts.append(f'<section id="{chapter_id}" class="chapter">')
        html_parts.append(f"<h2>{chapter_title}</h2>")

        for section_key, sections_data in chapitre_data.items():
            section_match = re.search(r"(\d+)", section_key)
            if section_match:
                section_number = int(section_match.group(1))
                section_title = _get_section_title(section_number)
                section_id = f"section_{section_number}"

                html_parts.append(f'<section id="{section_id}" class="section">')
                html_parts.append(f"<h3>{section_title}</h3>")

                if section_number == 10:
                    # Special handling for section 10
                    if sections_data and len(sections_data) > 0:
                        html_parts.append('<div class="rules">')
                        for regle in sections_data[0].get("regles", []):
                            html_parts.extend(_format_rule(regle))
                        html_parts.append("</div>")
                    else:
                        html_parts.append("<p>Aucune règle</p>")
                else:
                    # Regular sections
                    for sous_section in sections_data:
                        sous_section_num = sous_section.get("sous_section", "")
                        titre = sous_section.get("titre", "")

                        if sous_section_num or titre:
                            html_parts.append('<div class="subsection">')
                            html_parts.append(f"<h4>{sous_section_num} - {titre}</h4>")

                            rules = sous_section.get("regles", [])
                            if rules:
                                html_parts.append('<div class="rules">')
                                for regle in rules:
                                    html_parts.extend(_format_rule(regle))
                                html_parts.append("</div>")
                            html_parts.append("</div>")

                html_parts.append("</section>")

        html_parts.append("</section>")

    html_parts.append("</main>")

    # Add references section
    html_parts.append("</div>")

    return "\n".join(html_parts)


def _format_rule(regle: Dict[str, str]) -> List[str]:
    """Format a single rule as HTML."""
    parts = []
    contenu = _escape_html(regle.get("contenu", ""))
    page_source = _escape_html(regle.get("page_source", ""))

    parts.append('<div class="rule">')
    parts.append(f"<p>{contenu}")
    if page_source:
        parts.append(f' <span class="source">({page_source})</span>')
    parts.append("</p>")
    parts.append("</div>")

    return parts
