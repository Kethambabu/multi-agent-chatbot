"""
Text-to-Image generation agent (v2).

Generates images from text descriptions using Pollinations.AI API.
Completely FREE — no API key required, no signup, no cost.

Supported models:
- flux         : FLUX Schnell (fast, good quality)
- flux-realism : FLUX Realism (photo-realistic)
- turbo        : Turbo (fastest)
- flux-3d      : 3D render style
- flux-anime   : Anime/manga style
- any-dark     : Dark, moody art
"""

import logging
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests
from PIL import Image


logger = logging.getLogger(__name__)

# Output directory for generated images (project-root level)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "outputs" / "images"

# Available Pollinations.AI models
AVAILABLE_MODELS = {
    "flux":          "FLUX Schnell (Fast)",
    "flux-realism":  "FLUX Realism (Photo-realistic)",
    "turbo":         "Turbo (Fastest)",
    "flux-3d":       "3D Render Style",
    "flux-anime":    "Anime / Manga Style",
    "any-dark":      "Dark / Moody Art",
}


class Text2ImageV2Agent:
    """Agent for generating images from text prompts using Pollinations.AI.

    Features:
    - Uses Pollinations.AI API (FREE, no API key required)
    - Multiple model styles (FLUX, Turbo, Anime, 3D, etc.)
    - Configurable image dimensions (512–1280)
    - Saves generated images to disk with unique filenames
    - Returns structured dict response for pipeline compatibility
    - Comprehensive error handling and logging
    - Always enabled (no API key dependency)
    """

    # Pollinations.AI base URL
    API_BASE = "https://image.pollinations.ai/prompt"

    # Default generation parameters
    DEFAULT_MODEL = "flux"
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 1024
    DEFAULT_TIMEOUT = 120  # seconds — generation can take 10-30s

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        output_dir: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        config=None,  # Accept config param for compatibility — ignored
    ):
        """Initialize the text-to-image generation agent.

        Args:
            model: Pollinations.AI model ID (default: "flux").
                   One of: flux, flux-realism, turbo, flux-3d, flux-anime, any-dark
            width: Image width in pixels (512, 768, 1024, or 1280)
            height: Image height in pixels (512, 768, 1024, or 1280)
            output_dir: Directory to save generated images.
                        Defaults to <project_root>/outputs/images/
            timeout: HTTP request timeout in seconds (default: 120)
            config: Ignored. Accepted for API compatibility with other agents.
        """
        self.model = model if model in AVAILABLE_MODELS else self.DEFAULT_MODEL
        self.width = width
        self.height = height
        self.timeout = timeout
        self.enabled = True  # Always enabled — no API key needed

        # Set up output directory
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Initialized Text2ImageV2Agent: model=%s, size=%dx%d, output=%s",
            self.model,
            self.width,
            self.height,
            self.output_dir,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_image(self, prompt: str, **kwargs) -> dict:
        """Generate an image from a text prompt.

        Args:
            prompt: Text description for image generation. Be descriptive
                    for best results.
            **kwargs: Optional overrides:
                model (str): Override default model for this call.
                width (int): Override default width.
                height (int): Override default height.
                seed (int):  Fixed seed for reproducibility (-1 = random).
                enhance (bool): Auto-enhance prompt (default: False).

        Returns:
            dict with keys:
                status (str):      "success" or "error"
                image_path (str):  Absolute path to saved image (on success)
                image_url (str):   Pollinations URL that generated the image
                message (str):     Human-readable status message
        """
        # Validate prompt
        if not prompt or not prompt.strip():
            logger.warning("Empty prompt received")
            return {
                "status": "error",
                "image_path": None,
                "image_url": None,
                "message": "Prompt cannot be empty.",
            }

        prompt = prompt.strip()

        # Resolve parameters (kwargs override defaults)
        model = kwargs.get("model", self.model)
        width = kwargs.get("width", self.width)
        height = kwargs.get("height", self.height)
        seed = kwargs.get("seed", -1)
        enhance = kwargs.get("enhance", False)

        # Build Pollinations URL
        encoded_prompt = quote(prompt)
        url = (
            f"{self.API_BASE}/{encoded_prompt}"
            f"?model={model}&width={width}&height={height}"
            f"&nologo=true&enhance={str(enhance).lower()}"
        )
        if seed >= 0:
            url += f"&seed={seed}"

        logger.info(
            "Generating image: model=%s, size=%dx%d, prompt='%s'",
            model,
            width,
            height,
            prompt[:80] + "..." if len(prompt) > 80 else prompt,
        )

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                error_msg = f"Pollinations API returned HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "image_path": None,
                    "image_url": url,
                    "message": error_msg,
                }

            # Validate image data
            image = Image.open(BytesIO(response.content))
            image.verify()

            # Save to disk with unique filename
            filename = f"generated_{uuid.uuid4().hex[:12]}.png"
            filepath = self.output_dir / filename
            filepath.write_bytes(response.content)

            image_path = str(filepath.resolve())
            logger.info("Image saved: %s (%d bytes)", image_path, len(response.content))

            return {
                "status": "success",
                "image_path": image_path,
                "image_url": url,
                "message": f"Image generated successfully ({len(response.content) / 1024:.1f} KB)",
            }

        except requests.exceptions.Timeout:
            error_msg = "Image generation timed out. Please try again."
            logger.error(error_msg)
            return {
                "status": "error",
                "image_path": None,
                "image_url": url,
                "message": error_msg,
            }

        except requests.exceptions.ConnectionError:
            error_msg = "Connection error. Check your internet connection."
            logger.error(error_msg)
            return {
                "status": "error",
                "image_path": None,
                "image_url": url,
                "message": error_msg,
            }

        except Exception as e:
            error_msg = f"Image generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "image_path": None,
                "image_url": url if 'url' in dir() else None,
                "message": error_msg,
            }

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def list_models(self) -> dict:
        """Return available model IDs and their descriptions."""
        return AVAILABLE_MODELS.copy()

    def set_model(self, model: str):
        """Change the default model.

        Args:
            model: Pollinations model ID.

        Raises:
            ValueError: If model is not in AVAILABLE_MODELS.
        """
        if model not in AVAILABLE_MODELS:
            raise ValueError(
                f"Unknown model '{model}'. "
                f"Available: {', '.join(AVAILABLE_MODELS.keys())}"
            )
        self.model = model
        logger.info("Default model changed to %s", model)

    # ------------------------------------------------------------------
    # Resource management
    # ------------------------------------------------------------------

    def close(self):
        """No-op — no persistent connections to close."""
        logger.debug("Text2ImageV2Agent.close() called (no-op)")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
