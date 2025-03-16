"""
Module for cleaning text data extracted from architectural regulation PDFs.
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests
from loguru import logger
from tqdm import tqdm

# ------------------------------
# STEP 1 : Text cleaning functions
# ------------------------------


def clean_formatting(text: str) -> str:
    """
    Clean text extracted from architectural regulations PDFs.

    Args:
        text: Raw OCR text from PDF

    Returns:
        Cleaned text with headers, footers and other noise removed
    """
    # Remove image references
    # text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Remove headers and footers
    header_footer_patterns = [
        r"Plan Local d\'Urbanisme Intercommunal",
        r"PLUI approuvé le \d+/\d+/\d+.*?\d+/\d+/\d+",
        r"> PLUI approuvé le.*?$",
        r"PLUi approuvé le.*?$",
        r"Réglement pièces écrites",
        r"Réglement zone.*?$",
        r"TOME \d+\.\d+",
    ]

    for pattern in header_footer_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)

    # Remove page numbers
    # text = re.sub(r"\d+$", "", text, flags=re.MULTILINE)

    # Remove table of contents sections
    text = re.sub(r"CHAPITRE \d+ - .*?\.{3,} \d+", "", text)
    text = re.sub(r"ARTICLE \d+ - .*?\.{3,} \d+", "", text)
    text = re.sub(r"\d+\.\d+\. .*?\.{3,} \d+", "", text)

    # Supprimer la section spécifique du pied de page
    text = re.sub(
        r"L'AGENCE\s+D'URBANISME DE LA RÉGION GREENOBLOISE.*?grenoblealpemetropole\.fr.*?Identité : www\.studioplay\.fr",
        "",
        text,
        flags=re.DOTALL,
    )

    # Remove watermarks and version indicators
    text = re.sub(r"Derni�re actualisation :.*?$", "", text, flags=re.MULTILINE)

    # Handle hyphenated words split across lines
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    # Normalize whitespace: replace multiple spaces with a single space
    text = re.sub(r" +", " ", text)

    # Normalize multiple newlines to a maximum of two
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ------------------------------
# STEP 2: LLM Clean text files
# ------------------------------


def create_overlapping_chunks(text, chunk_size=4000, overlap=200):
    """
    Split text into overlapping chunks of specified size.

    Args:
        text (str): The text to be split into chunks
        chunk_size (int): Maximum size of each chunk in characters
        overlap (int): Number of characters to overlap between chunks

    Returns:
        list: List of text chunks
    """
    if not text:
        return []

    # Handle case where text is shorter than chunk_size
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        # Get chunk of size chunk_size
        end = min(start + chunk_size, len(text))

        # If not at the beginning of text, adjust start to maintain proper sentences
        if start > 0:
            # Try to find a sentence boundary in the overlap region
            overlap_start = max(0, start - overlap)
            overlap_text = text[overlap_start:start]
            sentence_boundaries = [
                m.start() + overlap_start
                for m in re.finditer(r"[.!?]\s+", overlap_text)
            ]

            if sentence_boundaries:
                # Start at the last sentence boundary in the overlap
                start = (
                    sentence_boundaries[-1] + 2
                )  # +2 to move past the punctuation and space

        # If not at the end, try to end at a sentence boundary
        if end < len(text):
            # Look for sentence boundary near the end of current chunk
            search_region = text[end - min(100, end) : end + min(100, len(text) - end)]
            sentence_end = search_region.find(". ")

            if sentence_end != -1:
                end = (
                    end - min(100, end) + sentence_end + 2
                )  # +2 to include the period and space

        # Extract chunk and add to list
        chunk = text[start:end]
        chunks.append(chunk)

        # Move to next chunk with overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks


def reassemble_chunks(cleaned_chunks, overlap=200):
    """
    Reassemble cleaned chunks into a single coherent text.

    Args:
        cleaned_chunks (list): List of cleaned text chunks
        overlap (int): Approximate overlap size used when creating chunks

    Returns:
        str: Reassembled text
    """
    if not cleaned_chunks:
        return ""

    if len(cleaned_chunks) == 1:
        return cleaned_chunks[0]

    result = cleaned_chunks[0]

    for i in range(1, len(cleaned_chunks)):
        current_chunk = cleaned_chunks[i]
        previous_chunk = result

        # Find the best joining point using fuzzy matching
        # We'll use a simplified approach here - find the largest common substring
        # near the end of the previous chunk and the start of the current chunk

        # Take the end of previous chunk and start of current chunk
        prev_end = previous_chunk[-min(len(previous_chunk), overlap * 2) :]
        curr_start = current_chunk[: min(len(current_chunk), overlap * 2)]

        # Find the largest common substring
        best_match_size = 0
        best_match_pos_prev = len(prev_end)
        best_match_pos_curr = 0

        for i in range(min(len(prev_end), len(curr_start))):
            for j in range(i + 1, min(len(prev_end), len(curr_start)) + 1):
                substring = prev_end[i:j]
                if (
                    len(substring) > 20 and substring in curr_start
                ):  # Only consider substrings > 20 chars
                    curr_pos = curr_start.find(substring)
                    if j - i > best_match_size:
                        best_match_size = j - i
                        best_match_pos_prev = len(previous_chunk) - len(prev_end) + i
                        best_match_pos_curr = curr_pos

        # If we found a good match, use it as the joining point
        if best_match_size > 20:
            result = (
                previous_chunk[:best_match_pos_prev]
                + current_chunk[best_match_pos_curr:]
            )
        else:
            # Fallback: simple concatenation with the last overlap removed
            result = result + " " + current_chunk

    return result


def setup_ollama_mistral(model_name="mistral:small", base_url="http://localhost:11434"):
    """
    Set up connection to Ollama for using Mistral Small model.

    Args:
        model_name (str): Name of the model to use in Ollama
        base_url (str): Base URL for Ollama API

    Returns:
        dict: Configuration for Ollama
    """
    try:
        # Check if model is available
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code != 200:
            logger.error(f"Failed to connect to Ollama API: {response.status_code}")
            return None

        available_models = response.json().get("models", [])
        model_names = [model.get("name") for model in available_models]

        if model_name not in model_names:
            logger.warning(
                f"Model {model_name} not found in Ollama. Available models: {model_names}"
            )
            logger.info(f"Attempting to pull {model_name}...")

            # Pull the model
            pull_response = requests.post(
                f"{base_url}/api/pull", json={"name": model_name}
            )

            if pull_response.status_code != 200:
                logger.error(
                    f"Failed to pull model {model_name}: {pull_response.status_code}"
                )
                return None

            # Wait for model to be pulled
            logger.info("Waiting for model to be ready...")
            time.sleep(5)  # Give it some time to initialize

        # Test the model with a simple generation
        test_response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model_name, "prompt": "Hello", "stream": False},
        )

        if test_response.status_code != 200:
            logger.error(f"Model test failed: {test_response.status_code}")
            return None

        logger.info(f"Successfully connected to Ollama with {model_name}")
        return {"model": model_name, "base_url": base_url}

    except Exception as e:
        logger.error(f"Error setting up Ollama: {str(e)}")
        return None


def get_cache_path(chunk, model_name):
    """Create a unique cache path for a chunk based on its content hash."""
    chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
    cache_dir = os.path.join("cache", "ollama", model_name.replace(":", "_"))
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{chunk_hash}.json")


def process_document_with_ollama(
    doc_text, ollama_config, chunk_size=4000, overlap=200, use_cache=True
):
    """
    Process document text in chunks with Ollama LLM for cleaning.

    Args:
        doc_text (str): Document text to clean
        ollama_config (dict): Ollama configuration from setup_ollama_mistral
        chunk_size (int): Size of each chunk to process
        overlap (int): Overlap between chunks
        use_cache (bool): Whether to use caching for processed chunks

    Returns:
        str: Cleaned document text
    """
    if not ollama_config:
        logger.error("Ollama configuration is missing. Cannot process document.")
        return doc_text

    model_name = ollama_config["model"]
    base_url = ollama_config["base_url"]

    # Create chunks
    logger.info("Creating document chunks...")
    chunks = create_overlapping_chunks(doc_text, chunk_size, overlap)
    logger.info(f"Created {len(chunks)} chunks from document")

    cleaned_chunks = []
    successful_chunks = 0

    for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
        cache_path = get_cache_path(chunk, model_name) if use_cache else None

        # Check cache first if enabled
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_result = json.load(f)
                    cleaned_chunks.append(cached_result["cleaned_text"])
                    successful_chunks += 1
                    logger.info(f"Chunk {i + 1}/{len(chunks)} loaded from cache")
                    continue
            except Exception as e:
                logger.warning(f"Failed to load from cache: {str(e)}")

        try:
            # Prepare architectural/legal domain-specific prompt
            prompt = f"""Below is text extracted from an architectural and urban planning legal document. Clean and structure it by:

1. Removing headers, footers, page numbers, and OCR artifacts
2. Preserving all legal information, including:
   - Article numbers and references
   - Zoning designations
   - Building specifications
   - Regulatory requirements
   - Land use restrictions
3. Maintaining the hierarchical structure of sections
4. Fixing hyphenated words split across lines
5. Standardizing formatting

ORIGINAL TEXT:
{chunk}

CLEANED TEXT:"""

            # Process with Ollama
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "frequency_penalty": 0.0,
                    },
                },
                timeout=60,  # 1-minute timeout
            )

            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}")
                cleaned_chunks.append(chunk)  # Fall back to original chunk
                continue

            result = response.json()
            cleaned_text = result.get("response", "").strip()

            # Cache the result if enabled
            if use_cache and cache_path:
                try:
                    with open(cache_path, "w") as f:
                        json.dump({"cleaned_text": cleaned_text}, f)
                except Exception as e:
                    logger.warning(f"Failed to write to cache: {str(e)}")

            cleaned_chunks.append(cleaned_text)
            successful_chunks += 1

        except Exception as e:
            logger.error(f"Error processing chunk {i + 1}/{len(chunks)}: {str(e)}")
            # Fall back to original chunk in case of error
            cleaned_chunks.append(chunk)

    logger.info(f"Successfully processed {successful_chunks}/{len(chunks)} chunks")

    # Reassemble the document
    logger.info("Reassembling document...")
    reassembled_text = reassemble_chunks(cleaned_chunks, overlap)

    return reassembled_text


def process_document(doc_path, output_path=None):
    """
    Process a document file with Ollama LLM.

    Args:
        doc_path (str): Path to the document file
        output_path (str, optional): Path to save the cleaned document

    Returns:
        str: Path to the cleaned document
    """
    try:
        # Read the document
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_text = f.read()

        # Set up Ollama
        ollama_config = setup_ollama_mistral()

        if not ollama_config:
            logger.error("Failed to set up Ollama. Cannot process document.")
            return None

        # Process the document
        cleaned_text = process_document_with_ollama(doc_text, ollama_config)

        # Save the cleaned document
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            logger.info(f"Saved cleaned document to {output_path}")
            return output_path

        return cleaned_text

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return None


# ------------------------------
# Final step: Clean text files
# ------------------------------


def clean_text_files(input_path: Path, output_dir: Path):
    """
    Process OCR result file in a directory.

    Args:
        input_dir: Directory containing OCR result file
        output_dir: Directory to save cleaned file.

    Returns:
        Statistics about processed files
    """

    md_files = list(input_path.glob("*.md"))

    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Clean the content
            cleaned_content = clean_formatting(content)

            output_file = output_dir / md_file.name
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_content)

        except Exception as e:
            print(f"Error processing {md_file}: {e}")
