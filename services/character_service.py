"""
Services for character and scene image generation.
"""
import base64
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from config import IMAGE_MODEL

load_dotenv()


class CharacterImageProcessor:
    """Handles character and scene generation using OpenAI image APIs."""

    def __init__(self, api_key: Optional[str] = None, model: str = IMAGE_MODEL):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is not configured.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_character_face(self, prompt: str, output_path: Path, size: str = "1024x1024") -> Path:
        """Generate a brand-new portrait from a text prompt."""
        if not prompt.strip():
            raise ValueError("Prompt is required to generate a character.")

        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
        )
        if not response.data or not response.data[0].b64_json:
            raise RuntimeError("OpenAI returned an empty response for image generation.")

        output_path.write_bytes(base64.b64decode(response.data[0].b64_json))
        return output_path

    def edit_image(
        self,
        image_path: Path,
        prompt: str,
        output_path: Path,
        size: str = "1536x1024",
    ) -> Path:
        """Use OpenAI image edit API to transform an image according to the prompt."""
        with image_path.open("rb") as image_file:
            response = self.client.images.edit(
                model=self.model,
                image=image_file,
                prompt=prompt,
                size=size,
            )

        if not response.data or not response.data[0].b64_json:
            raise RuntimeError("OpenAI returned an empty response for image edit.")

        output_path.write_bytes(base64.b64decode(response.data[0].b64_json))
        return output_path

    def generate_scene_image(
        self,
        base_image_path: Path,
        theme_prompt: str,
        output_path: Path,
        size: str = "1536x1024",
    ) -> Path:
        """Generate a themed scene image using the base image and prompt."""
        return self.edit_image(
            image_path=base_image_path,
            prompt=theme_prompt,
            output_path=output_path,
            size=size,
        )

