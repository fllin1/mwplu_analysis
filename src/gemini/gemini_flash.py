import re
from pathlib import Path
from typing import List, Optional, Tuple

import vertexai
from vertexai.generative_models import (
    Content,
    GenerationConfig,
    GenerationResponse,
    GenerativeModel,
    Part,
)


def split_markdown_by_images(markdown_text: str) -> Tuple[List[str], List[str]]:
    """
    Divides a markdown text into segments and image tags.

    Args:
        markdown_text: The markdown text to split.

    Returns:
        A tuple containing the segments and image tags.
    """
    # Motif regex pour capturer les balises d'images markdown : ![texte alternatif](chemin_image)
    pattern = r"(!\[.*?\]\(.*?\))"
    segments = re.split(pattern=pattern, string=markdown_text)
    image_tags = re.findall(pattern=pattern, string=markdown_text)
    return segments, image_tags


def extract_image_filename(image_tag: str) -> Optional[str]:
    """
    Extracts the image filename from an image tag.

    Args:
        image_tag: The image tag to extract the filename from.

    Returns:
        The image filename.
    """
    match = re.search(r"\]\((.*?)\)", image_tag)
    if match:
        return match.group(1)
    return None


def get_plu_ocr_data(user_message: str, path_dir: Path) -> List[any]:
    """
    Document data for the generative model.

    Args:
        user_message: The user message.
        path_dir: The path to the directory containing the user message.

    Returns:
        The user message and the parts of the generative model.
    """
    md_file = next(path_dir.glob("*md"))
    with open(md_file, "r") as f:
        document_content = f.read()

    # Format the user message with document content
    # Normalize newlines instead of completely removing them
    user_message = user_message.format(DOCUMENT_CONTENT=document_content)

    segments_message, image_tags = split_markdown_by_images(user_message)
    images_dir = path_dir / Path("images")
    final_parts: List[any] = []

    for segment in segments_message:
        if segment in image_tags:
            try:
                image_filename = extract_image_filename(segment)
                if image_filename:  # Only process if we have a valid filename
                    image_path = images_dir / Path(image_filename)
                    with open(image_path, "rb") as f:
                        image_bytes = f.read()
                        final_parts.append(
                            Part.from_data(data=image_bytes, mime_type="image/jpeg")
                        )
            except FileNotFoundError:
                continue
        elif segment.strip():  # Only add non-empty text segments
            final_parts.append(Part.from_text(segment))

    return final_parts


def generate_analysis(
    user_message: str,
    path_dir: Path,
    system_prompt: Optional[str] = None,
) -> GenerationResponse:
    """
    Generate the analysis of the PLU document.

    Args:
        user_message: The user message.
        path_dir: The path to the directory containing the user message.
        system_prompt: The system prompt.

    Returns:
        The generation response.
    """
    # Initialiser le client
    vertexai.init(
        project="analyse-plu",
        location="europe-west1",
    )

    # Créer le modèle
    model = GenerativeModel("gemini-2.0-flash-001")

    # Configuration de génération
    generation_config = GenerationConfig(
        temperature=1,
        top_p=0.95,
        max_output_tokens=8192,
        # # To get the response in JSON format
        # response_mime_type="application/json",
        # response_schema={
        #     "type": "OBJECT",
        #     "properties": {"response": {"type": "STRING"}},
        # },
    )

    # # Paramètres de sécurité
    # safety_settings = [
    #     types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
    #     types.SafetySetting(
    #         category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
    #     ),
    #     types.SafetySetting(
    #         category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
    #     ),
    #     types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
    # ]

    parts = get_plu_ocr_data(user_message=user_message, path_dir=path_dir)
    contents = [
        # Content(role="system", parts=[Part.from_text(system_prompt)]), NOTE: Sytem prompt not supported w/ gemini-2.0-flash-001
        Content(role="user", parts=[Part.from_text(system_prompt)] + parts),
    ]

    # Générer la réponse
    response: GenerationResponse = model.generate_content(
        contents=contents,
        generation_config=generation_config,
        # safety_settings=safety_settings,
        stream=False,
    )

    return response
