"""
Hugging Face Inference API client.

Provides a production-ready client for interacting with Hugging Face Inference API
with robust error handling, retries, timeouts, and logging.
"""

import logging
import time
import json
from typing import Dict, Union, Any, Optional
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import get_config


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class HFClientConfig:
    """Configuration for Hugging Face API client.
    
    Uses the new router-based Hugging Face inference API.
    Old endpoint (api-inference.huggingface.co) has been deprecated (410 errors).
    """
    
    api_key: Optional[str] = None
    base_url: str = "https://router.huggingface.co"
    api_path: str = "/hf-inference"  # Router namespace for HF inference
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_backoff_factor: float = 0.3  # seconds
    model_loading_timeout: int = 120  # for model loading delays


class HFAPIError(Exception):
    """Base exception for Hugging Face API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class HFModelLoadingError(HFAPIError):
    """Exception raised when model is still loading."""
    pass


class HFAPIAuthError(HFAPIError):
    """Exception raised for authentication errors."""
    pass


class HFAPITimeoutError(HFAPIError):
    """Exception raised for timeout errors."""
    pass


class HFClient:
    """Production-ready client for Hugging Face Inference API.
    
    Features:
    - Automatic retries with exponential backoff
    - Model loading delay handling
    - Configurable timeouts
    - JSON and binary response support
    - Comprehensive error handling and logging
    """
    
    def __init__(self, config: Optional[HFClientConfig] = None):
        """Initialize Hugging Face API client.
        
        Args:
            config: HFClientConfig instance. If None, creates default config
                   with API key from HF_API_KEY environment variable.
                   
        Raises:
            HFAPIAuthError: If no API key is provided or found in environment.
        """
        if config is None:
            root_config = get_config()
            config = HFClientConfig(
                api_key=root_config.hf_api_key,
                timeout=root_config.timeout,
                max_retries=root_config.max_retries,
                retry_backoff_factor=root_config.retry_backoff_factor,
                model_loading_timeout=root_config.model_loading_timeout
            )
        else:
            # If config exists but missing an API key, inherit from central config
            if not config.api_key:
                try:
                    config.api_key = get_config().hf_api_key
                except Exception:
                    pass

        api_key = config.api_key
        if not api_key:
            raise HFAPIAuthError(
                "Hugging Face API key not provided. "
                "Set HF_API_KEY environment variable or pass config.api_key"
            )
        
        self.config = config
        self.api_key = api_key
        self.session = self._create_session()
        
        logger.info(
            "Initialized Hugging Face API client with timeout=%ds, "
            "max_retries=%d, router_url=%s%s",
            config.timeout, 
            config.max_retries,
            config.base_url,
            config.api_path
        )
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy.
        
        Returns:
            Configured requests.Session with automatic retries.
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these codes
            allowed_methods=["POST", "GET"]  # Retry on these methods
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "HFClient/1.0"
        })
        
        return session
    
    def _handle_model_loading(self, response: requests.Response) -> bool:
        """Handle model loading delays (503 with specific headers).
        
        Args:
            response: HTTP response object.
            
        Returns:
            True if model is loading and client should retry, False otherwise.
            
        Raises:
            HFModelLoadingError: If model loading timeout exceeded.
        """
        if response.status_code != 503:
            return False
        
        # Check for model loading indicator
        if "loading" in response.text.lower():
            logger.warning("Model is loading, retrying after delay...")
            return True
        
        return False
    
    def request(
        self,
        model: str,
        payload: Optional[Dict[str, Any]] = None,
        task: str = "text-generation",
        return_json: bool = True,
        timeout: Optional[int] = None,
        raw_body: Optional[bytes] = None,
        content_type: str = "application/json"
    ) -> Union[Dict[str, Any], bytes]:
        """Make a request to Hugging Face Inference API via router endpoint.
        
        Args:
            model: Model identifier (e.g., "facebook/bart-large-cnn")
            payload: JSON request payload as dictionary
            task: Task type for API endpoint (used for logging only)
            return_json: If True, return parsed JSON; if False, return raw bytes
            timeout: Override default timeout in seconds
            raw_body: Optional raw bytes body for binary inputs
            content_type: Content-Type header for the request
            
        Returns:
            Parsed JSON response or raw bytes depending on return_json parameter.
            
        Raises:
            HFAPIAuthError: If authentication fails (401/403)
            HFAPITimeoutError: If request times out
            HFAPIError: For other API errors (404 model not found, 410 endpoint deprecated, etc.)
        """
        timeout_seconds = timeout or self.config.timeout
        # New router-based endpoint: https://router.huggingface.co/hf-inference/models/{model}
        url = f"{self.config.base_url}{self.config.api_path}/models/{model}"
        
        logger.debug(
            "Making request to model=%s, task=%s, timeout=%ds, url=%s",
            model,
            task,
            timeout_seconds,
            url
        )
        
        start_time = time.time()
        last_error = None
        
        # Implement custom retry logic for model loading timeout
        while time.time() - start_time < self.config.model_loading_timeout:
            try:
                request_args = {
                    "timeout": timeout_seconds,
                    "headers": {
                        "Content-Type": content_type
                    }
                }

                if raw_body is not None:
                    request_args["data"] = raw_body
                else:
                    request_args["json"] = payload or {}

                response = self.session.post(
                    url,
                    **request_args
                )
                logger.debug(
                    "HF response: status=%s, content_type=%s, bytes=%s",
                    response.status_code,
                    response.headers.get("Content-Type"),
                    len(response.content or b"")
                )
                
                # Handle model loading delay (503 Service Unavailable)
                if self._handle_model_loading(response):
                    logger.warning("Model loading, retrying in 2s...")
                    time.sleep(2)  # Wait before retrying
                    continue
                
                # Handle authentication errors (401/403)
                if response.status_code in (401, 403):
                    logger.error("Authentication failed (status %d): %s", response.status_code, response.text)
                    raise HFAPIAuthError(
                        f"Authentication failed: {response.status_code} - {response.text}",
                        status_code=response.status_code,
                        response_text=response.text
                    )
                
                # Handle model not found (404)
                if response.status_code == 404:
                    error_msg = f"Model not found: {model}. Status: 404. Response: {response.text}"
                    logger.error(error_msg)
                    raise HFAPIError(
                        error_msg,
                        status_code=404,
                        response_text=response.text
                    )
                
                # Handle endpoint deprecated (410)
                if response.status_code == 410:
                    error_msg = (
                        f"Endpoint deprecated (410 Gone). The old api-inference.huggingface.co "
                        f"has been replaced. Using router endpoint: {url}. "
                        f"Response: {response.text}"
                    )
                    logger.error(error_msg)
                    raise HFAPIError(
                        error_msg,
                        status_code=410,
                        response_text=response.text
                    )
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Parse and return response
                if return_json:
                    result = response.json()
                    logger.info("✓ Successfully received JSON response from model=%s", model)
                    return result
                else:
                    logger.info("✓ Successfully received bytes response (size=%d) from model=%s", len(response.content), model)
                    return response.content
                
            except requests.exceptions.Timeout as e:
                logger.error("Request timeout after %ds", timeout_seconds)
                raise HFAPITimeoutError(
                    f"Request timed out after {timeout_seconds}s"
                ) from e
            
            except requests.exceptions.HTTPError as e:
                response = getattr(e, 'response', None)
                status_code = response.status_code if response is not None else None
                response_text = response.text if response is not None else str(e)
                
                logger.error("HTTP error %d: %s", status_code, response_text)
                last_error = e

                # Permanent client errors (4xx) should fail fast (except 429 rate limit and 404/410 which are handled above)
                if status_code is not None and 400 <= status_code < 500 and status_code not in (429, 404, 410):
                    logger.error("Non-retriable HTTP error %s: %s", status_code, response_text)
                    raise HFAPIError(f"HTTP error {status_code}", status_code=status_code, response_text=response_text) from e

                # Retriable errors: 429 (rate limit), 500, 502, 503, 504
                if status_code in (429, 500, 502, 503, 504):
                    if time.time() - start_time < self.config.model_loading_timeout:
                        retry_wait = 2 ** min(3, int((time.time() - start_time) / 10))  # Exponential backoff
                        logger.warning("Retriable error %s, retrying in %ds...", status_code, retry_wait)
                        time.sleep(retry_wait)
                        continue
                
                # Non-retriable or timeout exceeded
                raise HFAPIError(
                    f"HTTP error {status_code}: {response_text}",
                    status_code=status_code,
                    response_text=response_text
                ) from e
            
            except requests.exceptions.RequestException as e:
                logger.error("Request failed: %s", e)
                raise HFAPIError(f"Request failed: {e}") from e
        
        # Model loading timeout exceeded
        logger.error(
            "Model loading timeout exceeded after %ds",
            self.config.model_loading_timeout
        )
        raise HFModelLoadingError(
            f"Model {model} did not finish loading within "
            f"{self.config.model_loading_timeout}s"
        )
    
    def text_generation(
        self,
        model: str,
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs
    ) -> Union[str, list]:
        """Generate text using a language model.
        
        Args:
            model: Model identifier
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            top_p: Nucleus sampling parameter
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text string or list of results depending on model response.
        """
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                **kwargs
            }
        }
        
        try:
            response = self.request(model, payload, task="text-generation")
            
            # Handle different response formats
            if isinstance(response, list) and len(response) > 0:
                # List of results, first one typically contains generated_text
                if isinstance(response[0], dict) and "generated_text" in response[0]:
                    text = response[0]["generated_text"]
                    logger.info("Generated text from %s", model)
                    return text
                return response
            
            logger.error("Unexpected response format: %s", response)
            raise HFAPIError(f"Unexpected response format: {response}")
            
        except HFAPIError as e:
            logger.error("Text generation failed: %s", e)
            raise
    
    def image_generation(
        self,
        model: str,
        prompt: str,
        height: int = 768,
        width: int = 768,
        num_inference_steps: int = 20,
        **kwargs
    ) -> bytes:
        """Generate an image using a vision model.
        
        Args:
            model: Model identifier
            prompt: Image description prompt
            height: Image height in pixels
            width: Image width in pixels
            num_inference_steps: Number of inference steps
            **kwargs: Additional generation parameters
            
        Returns:
            Image bytes (PNG or JPEG format)
        """
        payload = {
            "inputs": prompt,
            "parameters": {
                "height": height,
                "width": width,
                "num_inference_steps": num_inference_steps,
                **kwargs
            }
        }
        
        try:
            image_bytes = self.request(
                model,
                payload,
                task="text-to-image",
                return_json=False
            )
            if not image_bytes:
                raise HFAPIError("Received empty response body from Hugging Face image generation API")

            if not isinstance(image_bytes, (bytes, bytearray)):
                raise HFAPIError(f"Invalid image response type: {type(image_bytes).__name__}")

            image_bytes = bytes(image_bytes)

            # Some failures come back as JSON in a 200 response.
            maybe_json = image_bytes.lstrip()
            if maybe_json.startswith(b"{"):
                try:
                    error_payload = json.loads(maybe_json.decode("utf-8"))
                except Exception:
                    error_payload = None
                if isinstance(error_payload, dict) and error_payload.get("error"):
                    raise HFAPIError(f"Hugging Face image generation error: {error_payload.get('error')}")

            if not self._looks_like_image_bytes(image_bytes):
                raise HFAPIError("Response received, but payload is not a valid image byte stream")

            logger.info("Generated image from %s", model)
            return image_bytes
            
        except HFAPIError as e:
            logger.error("Image generation failed: %s", e)
            raise

    @staticmethod
    def _looks_like_image_bytes(image_bytes: bytes) -> bool:
        """Validate common image formats by magic bytes."""
        if len(image_bytes) < 12:
            return False

        signatures = (
            b"\x89PNG\r\n\x1a\n",  # PNG
            b"\xff\xd8\xff",       # JPEG
            b"GIF87a",             # GIF
            b"GIF89a",             # GIF
            b"RIFF",               # WEBP (RIFF....WEBP)
        )

        if image_bytes.startswith(signatures[0]):
            return True
        if image_bytes.startswith(signatures[1]):
            return True
        if image_bytes.startswith(signatures[2]) or image_bytes.startswith(signatures[3]):
            return True
        if image_bytes.startswith(signatures[4]) and image_bytes[8:12] == b"WEBP":
            return True
        return False
    
    def question_answering(
        self,
        model: str,
        question: str,
        context: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Answer a question based on provided context.
        
        Args:
            model: Model identifier
            question: The question
            context: Context passage containing the answer
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with answer and confidence score
        """
        payload = {
            "inputs": {
                "question": question,
                "context": context
            },
            "parameters": kwargs
        }
        
        try:
            response = self.request(model, payload, task="question-answering")
            logger.info("Question answered using %s", model)
            return response
            
        except HFAPIError as e:
            logger.error("Question answering failed: %s", e)
            raise
    
    def sentiment_analysis(
        self,
        model: str,
        text: str,
        **kwargs
    ) -> list:
        """Analyze sentiment of text.
        
        Args:
            model: Model identifier
            text: Text to analyze
            **kwargs: Additional parameters
            
        Returns:
            List of sentiment scores with labels and scores
        """
        payload = {
            "inputs": text,
            "parameters": kwargs
        }
        
        try:
            response = self.request(model, payload, task="text-classification")
            logger.info("Sentiment analyzed using %s", model)
            return response
            
        except HFAPIError as e:
            logger.error("Sentiment analysis failed: %s", e)
            raise
    
    def image_classification(
        self,
        model: str,
        image_bytes: bytes,
        **kwargs
    ) -> list:
        """Classify an image using the Hugging Face router inference endpoint.
        
        Args:
            model: Model identifier
            image_bytes: Raw image bytes
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response from the image classification model
        """
        try:
            response = self.request(
                model=model,
                raw_body=image_bytes,
                content_type="application/octet-stream",
                task="image-classification",
                return_json=True,
                timeout=self.config.timeout
            )
            logger.info("Classified image using %s", model)
            return response
        except HFAPIError as e:
            logger.error("Image classification failed: %s", e)
            raise
    
    def zero_shot_classification(
        self,
        model: str,
        text: str,
        candidate_labels: list,
        multi_class: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Classify text against candidate labels using zero-shot classification.
        
        Perfect for intent detection without training data.
        
        Args:
            model: Model identifier (e.g., "facebook/bart-large-mnli")
            text: Text to classify
            candidate_labels: List of label strings to classify against
            multi_class: If True, each label can be assigned independently
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with 'labels' (sorted by score) and 'scores' (confidence values)
            
        Example:
            >>> client = HFClient()
            >>> result = client.zero_shot_classification(
            ...     "facebook/bart-large-mnli",
            ...     "I want to summarize this article",
            ...     ["summarize text", "analyze image", "generate content"]
            ... )
            >>> print(result['labels'][0])  # Top label
            >>> print(result['scores'][0])  # Confidence score
        """
        payload = {
            "inputs": text,
            "parameters": {
                "candidate_labels": candidate_labels,
                "multi_class": multi_class,
                **kwargs
            }
        }
        
        try:
            response = self.request(
                model,
                payload,
                task="zero-shot-classification"
            )
            logger.info(
                "Zero-shot classification completed with %d labels using %s",
                len(candidate_labels),
                model
            )
            return response
            
        except HFAPIError as e:
            logger.error("Zero-shot classification failed: %s", e)
            raise
    
    def close(self):
        """Close the HTTP session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.info("Closed Hugging Face API client session")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def query_hf_model(
    model: str,
    payload: Dict[str, Any],
    task: str = "text-generation",
    return_json: bool = True,
    config: Optional[HFClientConfig] = None,
    timeout: Optional[int] = None,
) -> Union[Dict[str, Any], bytes]:
    """Query a Hugging Face hosted model with retry-safe inference.

    Args:
        model: Model identifier, e.g. "facebook/bart-large-cnn".
        payload: Inference payload for the model.
        task: Task type to use for the inference endpoint.
        return_json: If True, return parsed JSON; if False, return raw bytes.
        config: Optional HFClientConfig for custom API settings.
        timeout: Override the default request timeout.

    Returns:
        Parsed JSON or raw bytes response from the model.

    Raises:
        HFAPIError: When the inference request fails.
    """
    with HFClient(config=config) as client:
        return client.request(
            model=model,
            payload=payload,
            task=task,
            return_json=return_json,
            timeout=timeout,
        )
