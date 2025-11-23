"""
Character image editor using OpenAI's image edit endpoint, with optional video generation.
"""
import base64
import mimetypes
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import requests
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

# Load environment variables from .env if present
load_dotenv()

class CharacterImageEditor:
    """Edits an image using OpenAI's image edit endpoint and can generate a video from the result."""

    def _init_(self, api_key: Optional[str] = None, model: str = "gpt-image-1") -> None:
        """
        Args:
            api_key: Optional OpenAI API key. Defaults to OPENAI_API_KEY env variable.
            model:   Image model to use (default: gpt-image-1).
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY or pass api_key.")

        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_influencer_face(
        self,
        prompt: str,
        output_path: str,
        size: str = "1024x1024",
    ) -> Path:
        """
        Generate a base influencer-style portrait from a natural language description.

        Args:
            prompt:      Description of the desired influencer appearance.
            output_path: Path where the generated image will be saved.
            size:        Output size accepted by the image generation model (default: 1024x1024).

        Returns:
            Path to the saved generated image.
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string.")

        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            size=size,
        )

        if not response.data:
            raise RuntimeError("Received empty response from OpenAI.")

        image_data = response.data[0].b64_json
        if not image_data:
            raise RuntimeError("No image data returned in response.")

        output_file = Path(output_path)
        output_file.write_bytes(base64.b64decode(image_data))

        return output_file

    def edit_image(
        self,
        image_path: str,
        prompt: str,
        output_path: str,
        size: str = "1920x1080",
    ) -> Path:
        """
        Edit the image based on the supplied prompt.

        Args:
            image_path: Path to the source image file.
            prompt:     Description of desired changes.
            output_path:Path where the edited image will be saved.
            size:       Target image size (default: 1920x1080).

        Returns:
            Path to the saved edited image.
        """
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        with image_file.open("rb") as image:
            response = self.client.images.edit(
                model=self.model,
                image=image,
                prompt=prompt,
                size=size,
            )

        if not response.data:
            raise RuntimeError("Received empty response from OpenAI.")

        image_data = response.data[0].b64_json
        if not image_data:
            raise RuntimeError("No image data returned in response.")

        output_file = Path(output_path)
        output_file.write_bytes(base64.b64decode(image_data))

        return output_file

    def resize_image(
        self,
        image_path: str,
        output_path: str,
        size: Tuple[int, int] = (1280, 720),
        resample: int = Image.LANCZOS,
    ) -> Path:
        """
        Resize an existing image to the specified dimensions.

        Args:
            image_path: Path to the source image file.
            output_path: Path to save the resized image.
            size: Target size as (width, height).
            resample: Resampling filter (default: Image.LANCZOS).

        Returns:
            Path to the saved resized image.
        """
        source = Path(image_path)
        if not source.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with Image.open(source) as img:
            resized = img.resize(size, resample=resample)
            output_file = Path(output_path)
            resized.save(output_file)

        return output_file


if _name_ == "_main_":
    editor = CharacterImageEditor()

    influencer_prompt = (
        "Portrait of a stylish Mexican influencer with shoulder-length blonde hair, soft makeup, "
        "bright natural lighting, contemporary background, friendly confident expression."
    )
    # generated_image_path = editor.generate_influencer_face(
    #     prompt=influencer_prompt,
    #     output_path="influencer.png",
    #     size="1024x1024",
    # )
    # print(f"Generated influencer image saved to {generated_image_path}")

    podcast_prompt = (
        "Recreate this influencer hosting a podcast in a modern studio, with a professional microphone, "
        "warm ambient lighting, and subtle branded background. Keep the face and hairstyle unchanged."
    )
    # edited_image_path = editor.edit_image(
    #     image_path="influencer.png",
    #     prompt=podcast_prompt,
    #     output_path="influencer_podcast.png",
    #     size="1536x1024",
    # )
    

    # # Step 2: resize to 1280x720
    resized_image_path = editor.resize_image(
        image_path="influencer_podcast.png",
        output_path="output.jpeg",
        size=(1280,720),
    )
    print(f"Resized image saved to {resized_image_path}")