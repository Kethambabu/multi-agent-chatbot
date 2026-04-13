"""
Hugging Face Inference API Client - Documentation

## Overview

The HFClient is a production-ready Python client for interacting with the Hugging Face 
Inference API. It provides robust error handling, automatic retries, timeout management, 
and comprehensive logging.

## Features

✓ Automatic retries with exponential backoff
✓ Handles model loading delays
✓ Configurable timeouts and model loading timeout
✓ JSON and binary response support
✓ Comprehensive error handling with custom exceptions
✓ Detailed logging for debugging
✓ Context manager support for resource cleanup
✓ Environment variable support for API key
✓ Task-specific convenience methods

## Installation

Ensure you have the required dependency:
    pip install requests

Or install all requirements:
    pip install -r requirements.txt

## Setup

### 1. Set API Key

Export your Hugging Face API key as an environment variable:
    export HF_API_KEY="your_api_key_here"

Or on Windows (PowerShell):
    $env:HF_API_KEY = "your_api_key_here"

### 2. Import and Initialize

```python
from utils.hf_client import HFClient

# Use environment variable (HF_API_KEY)
client = HFClient()

# Or provide API key via config
from utils.hf_client import HFClientConfig

config = HFClientConfig(
    api_key="your_api_key",
    timeout=30,
    max_retries=3
)
client = HFClient(config=config)
```

## Configuration Options

```python
from utils.hf_client import HFClientConfig

config = HFClientConfig(
    api_key=None,  # Uses HF_API_KEY env var if None
    base_url="https://api-inference.huggingface.co",
    timeout=30,  # Request timeout in seconds
    max_retries=3,  # Number of retries for failed requests
    retry_backoff_factor=2.0,  # Exponential backoff multiplier
    model_loading_timeout=120  # Max time to wait for model loading
)
```

## Usage Examples

### Basic Text Generation

```python
from utils.hf_client import HFClient

with HFClient() as client:
    response = client.text_generation(
        model="mistralai/Mistral-7B-Instruct-v0.1",
        prompt="What is Python?",
        max_new_tokens=256,
        temperature=0.7
    )
    print(response)
```

### Image Generation

```python
with HFClient() as client:
    image_bytes = client.image_generation(
        model="stabilityai/stable-diffusion-2",
        prompt="A beautiful sunset over mountains",
        height=768,
        width=768
    )
    
    with open("image.png", "wb") as f:
        f.write(image_bytes)
```

### Question Answering

```python
with HFClient() as client:
    answer = client.question_answering(
        model="deepset/roberta-base-squad2",
        question="When was Python released?",
        context="Python was released in 1991 by Guido van Rossum."
    )
    print(answer)
```

### Sentiment Analysis

```python
with HFClient() as client:
    sentiment = client.sentiment_analysis(
        model="distilbert-base-uncased-finetuned-sst-2-english",
        text="I love this product!"
    )
    print(sentiment)
```

### Custom Requests

```python
with HFClient() as client:
    response = client.request(
        model="gpt2",
        payload={
            "inputs": "The capital of France is",
            "parameters": {"max_new_tokens": 10}
        },
        return_json=True
    )
```

## Error Handling

The client provides specific exception types for different error scenarios:

```python
from utils.hf_client import (
    HFClient,
    HFAPIError,
    HFAPIAuthError,
    HFAPITimeoutError,
    HFModelLoadingError
)

try:
    with HFClient() as client:
        response = client.text_generation(
            model="model-name",
            prompt="test"
        )
except HFAPIAuthError as e:
    print(f"Authentication failed: {e}")
except HFAPITimeoutError as e:
    print(f"Request timeout: {e}")
except HFModelLoadingError as e:
    print(f"Model loading timeout: {e}")
except HFAPIError as e:
    print(f"API error: {e}")
```

## Exception Types

- **HFAPIError**: Base exception for all Hugging Face API errors
- **HFAPIAuthError**: Authentication error (401/403 HTTP responses)
- **HFAPITimeoutError**: Request timeout exceeded
- **HFModelLoadingError**: Model loading timeout exceeded

## Retry Mechanism

The client automatically retries failed requests with exponential backoff:

- Retries on: 429 (Too Many Requests), 500, 502, 503, 504 errors
- Backoff formula: wait_time = backoff_factor ^ retry_attempt
- Default: 3 retries with 2.0x backoff factor

Configure retries:
```python
config = HFClientConfig(
    max_retries=5,
    retry_backoff_factor=1.5
)
```

## Model Loading Timeout

When a model is still loading on the server (503 with "loading" indicator), 
the client automatically retries until the model_loading_timeout is exceeded:

```python
config = HFClientConfig(
    model_loading_timeout=180  # 3 minutes
)
```

## Logging

Enable logging to see detailed client behavior:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log levels:
- **INFO**: Standard operations (requests, responses)
- **DEBUG**: Detailed request/response information
- **WARNING**: Retry and timeout warnings
- **ERROR**: Error conditions and exceptions

## Best Practices

1. **Use Context Manager**:
   ```python
   with HFClient() as client:
       response = client.text_generation(...)
   ```
   This ensures proper resource cleanup.

2. **Handle Exceptions**:
   Always handle specific exceptions for robustness:
   ```python
   try:
       response = client.text_generation(...)
   except HFModelLoadingError:
       # Retry with exponential backoff
       time.sleep(10)
   except HFAPITimeoutError:
       # Increase timeout or use larger models
       pass
   ```

3. **Configure Appropriate Timeouts**:
   - Large models may need longer timeouts
   - Increase `model_loading_timeout` for rarely-used models
   - Adjust `timeout` based on model size and complexity

4. **Monitor API Usage**:
   Enable INFO logging to track API calls:
   ```python
   logging.getLogger('utils.hf_client').setLevel(logging.INFO)
   ```

5. **Use Environment Variables**:
   Keep API keys out of code:
   ```python
   import os
   api_key = os.getenv("HF_API_KEY")
   ```

6. **Reuse Client Instance**:
   Create one client per application, not per request:
   ```python
   client = HFClient()
   response1 = client.text_generation(...)
   response2 = client.image_generation(...)
   client.close()
   ```

## Integration with Multi-Modal Agent

The client is designed to work seamlessly with the multi-modal agent framework:

```python
# In agents/text_generation_agent.py
from utils.hf_client import HFClient

class TextGenerationAgent:
    def __init__(self):
        self.client = HFClient()
    
    def process(self, prompt: str):
        return self.client.text_generation(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            prompt=prompt
        )
```

## Troubleshooting

### "API key not found or invalid"
- Check that HF_API_KEY environment variable is set
- Verify API key is valid at huggingface.co

### "Model loading timeout exceeded"
- Model is overloaded or doesn't exist
- Try increasing `model_loading_timeout`
- Use a smaller or more available model

### "Request timeout"
- Model response is slow
- Increase `timeout` parameter
- Use shorter prompt/fewer generation steps

### 429 (Too Many Requests)
- Hitting rate limits
- Requests are automatically retried
- Consider adding delay between requests

## Performance Tips

1. **Batch requests**: Send multiple requests in parallel for throughput
2. **Cache responses**: Store results to avoid redundant API calls
3. **Choose appropriate models**: Smaller models respond faster
4. **Monitor usage**: Keep track of API calls and costs
5. **Use async patterns**: Consider async/await for non-blocking calls

## API Reference

### HFClient Methods

#### text_generation(model, prompt, **kwargs)
Generate text using a language model.

#### image_generation(model, prompt, **kwargs)
Generate images using a vision model.

#### question_answering(model, question, context, **kwargs)
Answer questions based on context.

#### sentiment_analysis(model, text, **kwargs)
Analyze text sentiment.

#### request(model, payload, task, return_json, timeout)
Make custom API requests.

#### close()
Close the HTTP session.

## License

This client is part of the multi-modal agent project.
"""
