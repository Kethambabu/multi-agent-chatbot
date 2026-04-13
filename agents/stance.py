"""
Stance detection agent.

Analyzes and detects the stance (positive, negative, neutral) of text using
zero-shot classification with facebook/bart-large-mnli model.
"""

import logging
from typing import Optional

from utils.hf_client import HFClient, HFClientConfig, HFAPIError


logger = logging.getLogger(__name__)


class StanceAgent:
    """Agent for detecting stance in text using zero-shot classification.
    
    Features:
    - Uses facebook/bart-large-mnli for zero-shot classification
    - Detects positive, negative, and neutral stance
    - Returns top label with confidence score
    - Handles multi-label scenarios
    - Error handling and validation
    - Comprehensive logging
    - Resource cleanup with context manager
    """
    
    # Model identifier for zero-shot classification
    MODEL_NAME = "facebook/bart-large-mnli"
    
    # Default labels for stance classification
    DEFAULT_LABELS = ["positive", "negative", "neutral"]
    
    def __init__(
        self,
        config: Optional[HFClientConfig] = None,
        labels: Optional[list[str]] = None
    ):
        """Initialize the stance detection agent.
        
        Args:
            config: HFClientConfig for API client. If None, uses defaults with
                   HF_API_KEY from environment variable.
            labels: List of labels for zero-shot classification.
                   Defaults to ["positive", "negative", "neutral"]
                   
        Raises:
            HFAPIError: If initialization fails (e.g., missing API key)
            ValueError: If labels list is empty
        """
        if labels is not None and not labels:
            raise ValueError("Labels list cannot be empty")
        
        self.labels = labels or self.DEFAULT_LABELS.copy()
        
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
                "Initialized StanceAgent with model=%s, labels=%s",
                self.MODEL_NAME,
                self.labels
            )
        except HFAPIError as e:
            logger.error("Failed to initialize StanceAgent: %s", e)
            raise
    
    def detect_stance(self, text: str) -> dict:
        """Detect the stance of the provided text.
        
        Uses zero-shot classification to classify text into one of the
        configured labels with confidence scores.
        
        Args:
            text: Text to analyze for stance
            
        Returns:
            Dictionary with keys:
                - 'label': Top detected label (str)
                - 'confidence': Confidence score for top label (float 0-1)
                - 'all_scores': Dictionary mapping labels to scores {label: score}
                
        Raises:
            ValueError: If text is empty
            HFAPIError: If API call fails
            HFAPITimeoutError: If request times out
            HFModelLoadingError: If model takes too long to load
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        text = text.strip()
        
        # Warn if text is very short
        if len(text) < 10:
            logger.warning("Text is very short (%d chars)", len(text))
        
        logger.info("Detecting stance for text (%d characters)", len(text))
        
        try:
            # Prepare payload for zero-shot classification
            payload = {
                "inputs": text,
                "parameters": {
                    "candidate_labels": self.labels,
                    "multi_label": False  # Single label classification
                }
            }
            
            response = self.client.request(
                model=self.MODEL_NAME,
                payload=payload,
                task="zero-shot-classification",
                return_json=True
            )
            
            # Parse zero-shot classification response
            # Response format: list of label-score pairs
            # [{"label": "positive", "score": 0.82}, {"label": "neutral", "score": 0.09}, {"label": "negative", "score": 0.07}]
            
            logger.debug("Raw response from model: %s", response)
            
            # Validate response format
            if not isinstance(response, list):
                logger.error("Expected list response, got %s: %s", type(response), response)
                raise HFAPIError(f"Unexpected response format: expected list, got {type(response)}")
            
            if not response:
                logger.error("Empty response list from API")
                raise HFAPIError("Empty response from API")
            
            # Validate each item in the list
            for item in response:
                if not isinstance(item, dict) or "label" not in item or "score" not in item:
                    logger.error("Invalid item in response list: %s", item)
                    raise HFAPIError(f"Invalid response format: {response}")
            
            # Extract the label with the highest score
            best = max(response, key=lambda x: x["score"])
            
            logger.info("Selected label with highest score: %s (%.4f)", best["label"], best["score"])
            
            # Convert list of dicts to dictionary format {label: score}
            all_scores_dict = {item["label"]: item["score"] for item in response}
            
            # Return structured output
            result = {
                "label": best["label"],
                "confidence": best["score"],
                "all_scores": all_scores_dict
            }
            
            logger.info(
                "Stance detected: label=%s, confidence=%.4f",
                result["label"],
                result["confidence"]
            )
            
            return result
            
        except ValueError as e:
            logger.error("Validation error: %s", e)
            raise
        except HFAPIError as e:
            logger.error("API error during stance detection: %s", e)
            raise
    
    def detect_stance_batch(self, texts: list[str]) -> list[dict]:
        """Detect stance for multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of stance detection results
            
        Raises:
            ValueError: If texts list is empty
            HFAPIError: If any API call fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        logger.info("Detecting stance for batch of %d texts", len(texts))
        
        results = []
        for i, text in enumerate(texts, 1):
            try:
                logger.debug("Processing text %d/%d", i, len(texts))
                result = self.detect_stance(text)
                results.append(result)
            except HFAPIError as e:
                logger.error("Failed to process text %d: %s", i, e)
                # Optionally: continue with next text or re-raise
                raise
        
        logger.info("Batch stance detection complete: %d texts processed", len(results))
        return results
    
    def set_labels(self, labels: list[str]):
        """Update the labels for classification.
        
        Args:
            labels: New list of labels
            
        Raises:
            ValueError: If labels list is empty
        """
        if not labels:
            raise ValueError("Labels list cannot be empty")
        
        self.labels = labels
        logger.info("Updated labels: %s", labels)
    
    def close(self):
        """Close the API client and cleanup resources."""
        if self.client:
            self.client.close()
            logger.info("Closed StanceAgent")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
