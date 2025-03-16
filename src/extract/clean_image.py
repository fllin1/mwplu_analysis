"""Clean images based on similarity to reference images"""

import os
import shutil
from pathlib import Path

import imagehash
from PIL import Image


def get_image_hash(image_path: Path) -> str:
    """Get perceptual hash of an image"""
    with Image.open(image_path) as img:
        img_hash = imagehash.phash(img)
    return img_hash


def reference_images(references_dir: Path) -> dict:
    """Get perceptual hash of an image"""
    img_hashes = {}
    for img_file in os.listdir(references_dir):
        img_path = os.path.join(references_dir, img_file)
        img_hash = get_image_hash(img_path)
        img_hashes[img_file] = img_hash
    return img_hashes


def is_similar_to_reference(references_dir: Path, image_path: Path, threshold: int = 5):
    """Check if an image is similar to a reference image"""
    img_hash = get_image_hash(image_path)
    reference_hashes = reference_images(references_dir=references_dir)

    for ref_hash in reference_hashes.values():
        hash_diff = img_hash - ref_hash
        if hash_diff <= threshold:
            return True

    return False


def clean_images_files(
    references_dir: Path, input_dir: Path, output_dir: Path, threshold: int = 5
):
    """Filter images in a directory based on similarity to reference images"""
    for filename in os.listdir(input_dir):
        if filename.endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(input_dir, filename)
            is_similar = is_similar_to_reference(
                references_dir=references_dir, image_path=img_path, threshold=threshold
            )
            if not is_similar:
                output_path = os.path.join(output_dir, filename)
                shutil.copy(img_path, output_path)
