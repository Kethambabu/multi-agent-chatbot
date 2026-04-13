"""
Text summarization agent.

Provides text summarization using Hugging Face's BART model (facebook/bart-large-cnn).
Handles long text input and produces concise summaries.
"""

import logging
from typing import Optional

from utils.hf_client import HFClient, HFClientConfig, HFAPIError, HFAPITimeoutError, HFModelLoadingError


logger = logging.getLogger(__name__)


class SummarizerAgent:
    """Agent for summarizing text content using Hugging Face BART model.
    
    Features:
    - Uses facebook/bart-large-cnn for high-quality summarization
    - Falls back to sshleifer/distilbart-cnn-12-6 if the primary model is unavailable
    - Handles long documents by chunking and merging summaries
    - Configurable summary length
    - Error handling and logging
    - Resource cleanup with context manager
    """
    
    # Model identifiers
    MODEL_NAME = "facebook/bart-large-cnn"
    FALLBACK_MODELS = ["sshleifer/distilbart-cnn-12-6"]
    
    # Default summarization parameters
    DEFAULT_MIN_LENGTH = 50
    DEFAULT_MAX_LENGTH = 150
    
    def __init__(
        self,
        config: Optional[HFClientConfig] = None,
        min_length: int = DEFAULT_MIN_LENGTH,
        max_length: int = DEFAULT_MAX_LENGTH
    ):
        """Initialize the summarizer agent.
        
        Args:
            config: HFClientConfig for API client. If None, uses defaults with
                   HF_API_KEY from environment variable.
            min_length: Minimum length of summary in tokens (default: 50)
            max_length: Maximum length of summary in tokens (default: 150)
            
        Raises:
            HFAPIError: If initialization fails (e.g., missing API key)
        """
        try:
            # Handle optional HFClientConfig and main Config objects
            if config is None:
                hf_config = HFClientConfig()
            elif hasattr(config, 'api_key'):
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
            self.min_length = min_length
            self.max_length = max_length
            
            logger.info(
                "Initialized SummarizerAgent with model=%s, "
                "min_length=%d, max_length=%d",
                self.MODEL_NAME,
                min_length,
                max_length
            )
        except HFAPIError as e:
            logger.error("Failed to initialize SummarizerAgent: %s", e)
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split text into smaller chunks for processing.
        
        BART has a maximum input length of ~1024 tokens. This method
        chunks text to ensure inputs stay within limits while preserving
        sentence boundaries.
        
        Args:
            text: Text to chunk
            chunk_size: Approximate size of each chunk in characters
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences (simple approach)
        sentences = text.replace(".", ".\n").replace("!", "!\n").split("\n")
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.debug("Chunked text into %d segments", len(chunks))
        return chunks
    
    def summarize(self, text: str) -> str:
        """Summarize the provided text using BART model.
        
        For long texts, splits into chunks, summarizes each, and returns
        the concatenated summaries.
        
        Args:
            text: Text to summarize. Should be at least a few sentences.
                 
        Returns:
            Summarized text
            
        Raises:
            ValueError: If text is empty or too short
            HFAPIError: If API call fails
            HFAPITimeoutError: If request times out
            HFModelLoadingError: If model takes too long to load
        """
        # Validate input
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        text = text.strip()
        
        if len(text) < 50:
            logger.warning("Text is very short (%d chars), returning as-is", len(text))
            return text
        
        logger.info("Starting summarization of text (%d characters)", len(text))
        
        try:
            # Chunk text if necessary
            chunks = self._chunk_text(text)
            
            # If only one chunk, summarize directly
            if len(chunks) == 1:
                return self._summarize_single(chunks[0])
            
            # For multiple chunks, summarize each and merge into a final summary
            logger.info("Text requires %d chunks for summarization", len(chunks))
            summaries = []
            
            for i, chunk in enumerate(chunks, 1):
                logger.debug("Summarizing chunk %d/%d", i, len(chunks))
                summaries.append(self._summarize_single(chunk))
            
            combined_summary = " ".join(summaries)
            logger.info(
                "Chunk summarization complete: %d chunks -> %d chars",
                len(chunks),
                len(combined_summary)
            )
            
            # Perform a second pass on the merged chunk summaries to improve coherence
            logger.info("Merging chunk summaries into a final summary")
            final_summary = self._summarize_single(combined_summary)
            logger.info(
                "Summarization complete: %d chunks -> %d chars final summary",
                len(chunks),
                len(final_summary)
            )
            return final_summary
            
        except ValueError as e:
            logger.error("Validation error: %s", e)
            raise
        except HFAPIError as e:
            logger.error("API error during summarization: %s", e)
            raise
    
    def _summarize_single(self, text: str) -> str:
        """Summarize a single text chunk.
        
        Args:
            text: Text chunk to summarize
            
        Returns:
            Summary text
            
        Raises:
            HFAPIError: If API call fails
        """
        payload = {
            "inputs": text,
            "parameters": {
                "min_length": self.min_length,
                "max_length": self.max_length,
                "do_sample": False  # Use deterministic beam search
            }
        }
        
        try:
            return self._call_summarization_model(self.MODEL_NAME, payload)
        except HFAPIError as e:
            logger.warning(
                "Primary summarization model %s failed: %s",
                self.MODEL_NAME,
                e
            )

            for fallback_model in self.FALLBACK_MODELS:
                try:
                    logger.info("Trying fallback summarization model %s", fallback_model)
                    return self._call_summarization_model(fallback_model, payload)
                except HFAPIError as fallback_error:
                    logger.warning(
                        "Fallback model %s failed: %s",
                        fallback_model,
                        fallback_error
                    )

            logger.error(
                "All summarization models failed for current text chunk."
            )
            raise

    def _call_summarization_model(self, model: str, payload: dict) -> str:
        response = self.client.request(
            model=model,
            payload=payload,
            task="summarization",
            return_json=True
        )

        # Extract summary from response
        if isinstance(response, list) and len(response) > 0:
            if isinstance(response[0], dict) and "summary_text" in response[0]:
                summary = response[0]["summary_text"]
                logger.debug("Generated summary from %s: %s", model, summary[:100])
                return summary

        logger.warning("Unexpected response format from %s: %s", model, response)
        return payload["inputs"]
    
    def close(self):
        """Close the API client and cleanup resources."""
        if self.client:
            self.client.close()
            logger.info("Closed SummarizerAgent")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
