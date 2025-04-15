from pathlib import Path
from typing import List, Union

import typer
from loguru import logger
from pypdf import PdfReader, PdfWriter

from src.config import EXTERNAL_DATA_DIR, INTERIM_DATA_DIR

app = typer.Typer(help="Outil pour extraire des pages d’un PDF.")


def parse_page_ranges(pages: str) -> List[int]:
    """
    Parses a string of page ranges and returns a list of page numbers.
    Args:
        pages (str): A string representing page ranges, e.g. "1,3-5,7".
    Returns:
        list[int]: A list of page numbers.
    """
    page_numbers = []
    for part in pages.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            page_numbers.extend(range(start - 1, end))
        else:
            page_numbers.append(int(part) - 1)
    return page_numbers


@app.command()
def extract(
    folder: str = typer.Option(
        "grenoble", "--folder", "-f", help="Dossier contenant le PDF source."
    ),
    input_pdf: Path = typer.Argument(..., help="Chemin du PDF source."),
    output_pdf: Path = typer.Argument(..., help="Chemin du PDF de sortie."),
    pages: str = typer.Option(
        ..., "--pages", "-p", help="Pages à extraire, ex : '1,3-5,7'"
    ),
) -> None:
    """
    Extracts specific pages from a PDF file and saves them to a new PDF file.
    Args:
        folder (str): The folder containing the source PDF file.
        input_pdf (Path): The path to the source PDF file.
        output_pdf (Path): The path to the output PDF file.
        pages (Union[str, List[int]]): The pages to extract, e.g. "1,3-5,7".
    """
    reader = PdfReader(
        str(EXTERNAL_DATA_DIR / Path(f"{folder}/{input_pdf}").with_suffix(".pdf"))
    )
    writer = PdfWriter()
    if type(pages) is str:
        page_indices = parse_page_ranges(pages)
    else:
        page_indices = pages

    for i in page_indices:
        writer.add_page(reader.pages[i])

    output_path = INTERIM_DATA_DIR / Path(f"{folder}/{output_pdf}").with_suffix(".pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f_out:
        writer.write(f_out)


if __name__ == "__main__":
    app()
