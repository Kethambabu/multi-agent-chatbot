"""
Image analysis agent.

Analyzes images and extracts information using Hugging Face's Vision Transformer model.
Performs image classification and returns top predictions.
"""

import logging
from typing import Optional
import io

from utils.hf_client import HFClient, HFClientConfig, HFAPIError


logger = logging.getLogger(__name__)


class ImageAnalysisAgent:
    """Agent for analyzing images and extracting information using ViT.
    
    Features:
    - Uses google/vit-base-patch16-224 for image classification
    - Accepts image bytes or file paths
    - Returns top predictions with confidence scores
    - Configurable number of top predictions to return
    - Error handling and validation
    - Comprehensive logging
    - Resource cleanup with context manager
    """
    
    # Model identifier for image classification
    MODEL_NAME = "google/vit-base-patch16-224"
    
    # ImageNet class count
    DEFAULT_TOP_K = 5
    
    def __init__(
        self,
        config: Optional[HFClientConfig] = None,
        top_k: int = DEFAULT_TOP_K
    ):
        """Initialize the image analysis agent.
        
        Args:
            config: HFClientConfig for API client. If None, uses defaults with
                   HF_API_KEY from environment variable.
            top_k: Number of top predictions to return (default: 5)
                   
        Raises:
            HFAPIError: If initialization fails (e.g., missing API key)
            ValueError: If top_k is not positive
        """
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        
        self.top_k = top_k
        
        try:
            # Handle both HFClientConfig and main Config objects
            if hasattr(config, 'api_key'):
                # Already HFClientConfig
                hf_config = config
            else:
                # Main Config object, create HFClientConfig
                hf_config = HFClientConfig(
                    api_key=config.hf_api_key,
                    timeout=config.timeout,
                    max_retries=config.max_retries,
                    retry_backoff_factor=config.retry_backoff_factor
                )
            self.client = HFClient(config=hf_config)
            logger.info(
                "Initialized ImageAnalysisAgent with model=%s, top_k=%d",
                self.MODEL_NAME,
                top_k
            )
        except HFAPIError as e:
            logger.error("Failed to initialize ImageAnalysisAgent: %s", e)
            raise
    
    def analyze_image(self, image_bytes: bytes) -> list:
        """Analyze an image and return top predictions.
        
        Args:
            image_bytes: Binary image data (PNG, JPEG, etc.)
                        
        Returns:
            List of predictions sorted by score (highest first).
            Each prediction is a dict with:
                - 'label': Classification label (str)
                - 'score': Confidence score (float 0-1)
                
        Raises:
            ValueError: If image_bytes is empty or invalid
            HFAPIError: If API call fails
            HFAPITimeoutError: If request times out
            HFModelLoadingError: If model takes too long to load
        """
        # Validate input
        if not image_bytes or len(image_bytes) == 0:
            raise ValueError("Image bytes cannot be empty")
        
        logger.info("Analyzing image (%d bytes)", len(image_bytes))
        
        try:
            result = self.client.image_classification(
                model=self.MODEL_NAME,
                image_bytes=image_bytes
            )

            # Handle response format from image classification
            # Response format: list of dicts with 'label' and 'score' keys
            if not isinstance(result, list):
                logger.error("Unexpected response format: %s", result)
                raise HFAPIError(f"Unexpected response format: {result}")

            # Sort by score (descending) and return top_k
            sorted_results = sorted(
                result,
                key=lambda x: x.get('score', 0),
                reverse=True
            )

            top_predictions = sorted_results[:self.top_k]

            # Format results with rounded scores
            formatted_results = [
                {
                    "label": pred.get("label", "unknown"),
                    "score": round(float(pred.get("score", 0)), 4)
                }
                for pred in top_predictions
            ]

            logger.info(
                "Image analysis complete: found %d labels, top prediction: %s (%.4f%%)",
                len(sorted_results),
                formatted_results[0].get("label") if formatted_results else "N/A",
                formatted_results[0].get("score", 0) * 100 if formatted_results else 0
            )

            return formatted_results
            
        except ValueError as e:
            logger.error("Validation error: %s", e)
            raise
        except HFAPIError as e:
            logger.error("API error during image analysis: %s", e)
            raise
    
    def analyze_image_file(self, filepath: str) -> list:
        """Analyze an image from a file path.
        
        Args:
            filepath: Path to image file (PNG, JPEG, etc.)
                     
        Returns:
            List of top predictions with confidence scores
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
            HFAPIError: If analysis fails
        """
        try:
            # Read image file
            with open(filepath, "rb") as f:
                image_bytes = f.read()
            
            logger.info("Analyzing image from file: %s", filepath)
            return self.analyze_image(image_bytes)
            
        except FileNotFoundError as e:
            logger.error("Image file not found: %s", filepath)
            raise
        except IOError as e:
            logger.error("Failed to read image file: %s", e)
            raise
    
    def analyze_batch(self, image_data_list: list) -> list:
        """Analyze multiple images.
        
        Args:
            image_data_list: List of image bytes or filepaths.
                            Can be:
                            - Raw bytes
                            - String filepaths
                            
        Returns:
            List of analysis results (list of predictions per image)
            
        Raises:
            ValueError: If list is empty
            HFAPIError: If any analysis fails
        """
        if not image_data_list:
            raise ValueError("Image data list cannot be empty")
        
        logger.info("Batch analyzing %d images", len(image_data_list))
        
        results = []
        for i, image_data in enumerate(image_data_list, 1):
            try:
                logger.debug("Processing image %d/%d", i, len(image_data_list))
                
                # Handle both bytes and filepaths
                if isinstance(image_data, str):
                    # It's a filepath
                    predictions = self.analyze_image_file(image_data)
                elif isinstance(image_data, bytes):
                    # It's already bytes
                    predictions = self.analyze_image(image_data)
                else:
                    logger.warning(
                        "Skipping image %d: unsupported type %s",
                        i,
                        type(image_data)
                    )
                    continue
                
                results.append({
                    "index": i - 1,
                    "predictions": predictions,
                    "status": "success"
                })
                
            except (ValueError, HFAPIError, IOError) as e:
                logger.error("Failed to analyze image %d: %s", i, e)
                results.append({
                    "index": i - 1,
                    "error": str(e),
                    "status": "failed"
                })
        
        logger.info("Batch analysis complete: %d succeeded", 
                   sum(1 for r in results if r.get("status") == "success"))
        return results
    
    def get_predictions(self, image_bytes: bytes) -> list:
        """Alias for analyze_image for consistency.
        
        Args:
            image_bytes: Binary image data
            
        Returns:
            List of predictions
        """
        return self.analyze_image(image_bytes)
    
    def set_top_k(self, top_k: int):
        """Update the number of top predictions to return.
        
        Args:
            top_k: Number of top predictions
            
        Raises:
            ValueError: If top_k is not positive
        """
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        
        self.top_k = top_k
        logger.info("Updated top_k to %d", top_k)
    
    def close(self):
        """Close the API client and cleanup resources."""
        if self.client:
            self.client.close()
            logger.info("Closed ImageAnalysisAgent")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
