"""
Service for external video generation API.
"""
from pathlib import Path
from typing import Dict, Any

import mimetypes
import requests

from config import (
    VIDEO_API_URL,
    VIDEO_API_EMAIL,
    VIDEO_API_SECRET,
    VIDEO_API_NAME,
)


def generate_video(prompt: str, image_path: Path) -> Dict[str, Any]:
    """
    Call the external video generation API using the provided prompt and image.

    Args:
        prompt: Text prompt for the video.
        image_path: Path to the reference image file (must exist).

    Returns:
        Parsed JSON response from the API.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image for video generation not found: {image_path}")

    mime, _ = mimetypes.guess_type(str(image_path))
    content_type = mime or "application/octet-stream"

    with image_path.open("rb") as image_file:
        files = {
            "image": (image_path.name, image_file, content_type),
        }
        data = {
            "prompt": prompt,
            "email": VIDEO_API_EMAIL,
            "secret": VIDEO_API_SECRET,
            "name": VIDEO_API_NAME,
        }
        response = requests.post(
            VIDEO_API_URL,
            data=data,
            files=files,
            timeout=120,
        )

    response.raise_for_status()
    return response.json()

