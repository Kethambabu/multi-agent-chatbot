"""
FastAPI Backend Documentation

Complete guide to running and using the Multi-Modal Agent API.
"""

# ============================================================================
# BACKEND API DOCUMENTATION
# ============================================================================

"""
## Multi-Modal Agent FastAPI Backend

A production-ready REST API for processing text and images through a unified
LangGraph workflow with intelligent task routing.

### Quick Start

#### 1. Installation
```bash
pip install -r requirements.txt
```

#### 2. Set Environment Variables
```bash
# Required
export HF_API_KEY="your-hugging-face-api-key"

# Optional (with defaults)
export DEBUG="False"
export API_HOST="0.0.0.0"
export API_PORT="8000"
export API_RELOAD="False"
export HF_TIMEOUT="30"
export HF_MAX_RETRIES="3"
export HF_MODEL_LOADING_TIMEOUT="120"
export MAX_IMAGE_SIZE="52428800"  # 50MB
export MAX_BATCH_SIZE="100"
```

#### 3. Run the Server
```bash
python backend.py
```

The API will start on http://localhost:8000

#### 4. Access Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Info**: http://localhost:8000/

---

### API Endpoints

#### Health & Info

**GET /health**
- Check API health and workflow status
- No authentication required
- Returns: {status, version, message}

**GET /**
- Get API information and available endpoints
- Returns: API name, version, description, endpoint list

---

#### Main Processing Endpoint

**POST /process**

Process text and optional image through the multi-modal workflow.

**Request Parameters (Form Data):**
- `text` (string, required): Input text (1-10000 chars)
- `image` (file, optional): Image file for analysis
- `verbose` (boolean, optional): Enable verbose logging

**Response:**
```json
{
  "success": true,
  "task_type": "summary|stance|image_gen|image_analysis",
  "result": {
    "type": "summary|stance|image|analysis",
    "content": "...",
    "status": "success"
  },
  "error": null,
  "messages": ["execution trace..."],
  "metadata": {
    "execution_failed": false,
    "has_image": false,
    "result_type": "summary"
  }
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/process \
  -F "text=Summarize this article about AI..." \
  -F "verbose=true"
```

**Example (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/process",
    data={"text": "Your text here", "verbose": True}
)
result = response.json()
print(result["task_type"])
print(result["result"]["content"])
```

---

#### Image Generation with Download

**POST /process-and-download**

Process text for image generation and download the image directly.

**Request Parameters (Form Data):**
- `text` (string, required): Image generation prompt
- `verbose` (boolean, optional): Enable verbose logging

**Response:**
- If image generated: Binary image/png with attachment header
- Otherwise: JSON ProcessResponse

**Example (curl):**
```bash
curl -X POST http://localhost:8000/process-and-download \
  -F "text=A serene mountain landscape at sunset" \
  -o generated_image.png
```

**Example (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/process-and-download",
    data={"text": "A beautiful sunset"}
)

if 'image' in response.headers['content-type']:
    with open('image.png', 'wb') as f:
        f.write(response.content)
else:
    print(response.json())
```

---

#### Batch Processing

**POST /process-batch**

Process multiple texts efficiently in batch mode.

**Request Parameters (Form Data):**
- `texts` (list[string], required): List of texts to process (max 100)

**Response:**
```json
{
  "total": 5,
  "successful": 4,
  "results": [
    {
      "index": 0,
      "success": true,
      "task_type": "summary",
      "result": {...},
      "error": null
    },
    ...
  ]
}
```

**Example (Python):**
```python
import requests

texts = [
    "Summarize this article...",
    "What's the sentiment?",
    "Analyze this image..."
]

response = requests.post(
    "http://localhost:8000/process-batch",
    data={"texts": texts}
)

result = response.json()
print(f"Processed: {result['successful']}/{result['total']}")
```

---

### Task Type Detection

The workflow automatically detects the task based on input:

| Task Type | Detection Criteria |
|-----------|-------------------|
| **IMAGE_ANALYSIS** | Image provided OR keywords: analyze, describe, identify, classify |
| **SUMMARIZATION** | Keywords: summarize, summary, condense, abstract (default if no match) |
| **IMAGE_GENERATION** | Keywords: generate, create, draw, design |
| **STANCE_DETECTION** | Keywords: opinion, sentiment, believe, agree |

---

### Configuration

#### Environment Variables

```
# HuggingFace API
HF_API_KEY              API key for HuggingFace Inference API
HF_TIMEOUT              Request timeout in seconds (default: 30)
HF_MAX_RETRIES          Retry attempts for failed requests (default: 3)
HF_MODEL_LOADING_TIMEOUT Timeout for model loading (default: 120)

# API Server
API_HOST                Server host (default: 0.0.0.0)
API_PORT                Server port (default: 8000)
API_RELOAD              Enable auto-reload on code changes (default: False)
API_WORKERS             Number of worker processes (default: 4)

# Application
DEBUG                   Enable debug mode (default: False)
MODEL_NAME              Model identifier (default: default-model)

# Limits
MAX_IMAGE_SIZE          Max image upload size in bytes (default: 50MB)
MAX_BATCH_SIZE          Max batch size for /process-batch (default: 100)
```

#### Config Class

The `Config` class in `config.py` loads and validates all settings:

```python
from config import Config

config = Config()
config.validate()  # Raises error if HF_API_KEY not set

# Access settings
print(config.hf_api_key)
print(config.api_host)
print(config.api_port)
```

---

### Error Handling

#### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Processing completed successfully |
| 400 | Bad Request | Invalid input (empty text, oversized request) |
| 500 | Server Error | Processing failed (LLM error, timeout) |
| 503 | Service Unavailable | Workflow not initialized |

#### Response Format (on Error)

```json
{
  "detail": "Error message explaining what went wrong"
}
```

#### Common Error Cases

**Empty Text:**
```bash
curl -X POST http://localhost:8000/process -F "text="
# Returns: 400 Bad Request
```

**Text Too Long:**
```bash
# Text exceeds 10000 chars
# Returns: 400 Bad Request - "Text exceeds maximum length"
```

**Image Too Large:**
```bash
# Image exceeds 50MB
# Returns: 400 Bad Request - "Image file too large"
```

**Workflow Not Initialized:**
```bash
# API started before workflow built
# Returns: 503 Service Unavailable
```

**Processing Failure:**
```json
{
  "success": false,
  "task_type": "summary",
  "error": "Processing failed: Timeout waiting for model",
  "messages": ["execution trace..."]
}
```

---

### Usage Examples

#### Example 1: Simple Text Summarization

```python
import requests

text = "Long article about AI that needs summarizing..."

response = requests.post(
    "http://localhost:8000/process",
    data={"text": text}
)

result = response.json()
if result["success"]:
    print(f"Summary: {result['result']['content']}")
else:
    print(f"Error: {result['error']}")
```

#### Example 2: Sentiment Analysis

```python
import requests

texts = [
    "I love this product!",
    "This is terrible.",
    "It's okay, nothing special."
]

for text in texts:
    response = requests.post(
        "http://localhost:8000/process",
        data={"text": text}
    )
    
    result = response.json()
    if result["success"]:
        stance = result["result"]["content"]
        print(f"{text} → {stance['label']} ({stance['confidence']:.1%})")
```

#### Example 3: Image Generation

```python
import requests
from pathlib import Path

prompt = "A serene mountain landscape at sunset with golden light"

response = requests.post(
    "http://localhost:8000/process-and-download",
    data={"text": prompt}
)

if 'image' in response.headers.get('content-type', ''):
    Path('generated_image.png').write_bytes(response.content)
    print("Image saved!")
else:
    print(f"Error: {response.json()['error']}")
```

#### Example 4: Image Analysis

```python
import requests

with open('photo.jpg', 'rb') as img:
    response = requests.post(
        "http://localhost:8000/process",
        data={"text": "Analyze this image"},
        files={"image": img}
    )

result = response.json()
if result["success"]:
    predictions = result["result"]["content"]
    for pred in predictions[:3]:
        print(f"{pred['label']}: {pred['score']:.1%}")
```

#### Example 5: Batch Processing

```python
import requests

texts = [
    "Summarize this article...",
    "Analyze my mood from this: I'm happy!",
    "Generate an image of a sunset"
]

response = requests.post(
    "http://localhost:8000/process-batch",
    data={"texts": texts}
)

result = response.json()
print(f"Processed: {result['successful']}/{result['total']}")

for item in result['results']:
    if item['success']:
        print(f"#{item['index']}: {item['task_type']} ✓")
    else:
        print(f"#{item['index']}: {item['error']} ✗")
```

---

### Performance Tips

1. **Batch Processing**: Use `/process-batch` for multiple texts (more efficient)
2. **Async Requests**: Use async HTTP client for concurrent requests
3. **Timeouts**: Set appropriate timeouts based on task type:
   - Text tasks: 30 seconds
   - Image generation: 60+ seconds
4. **Caching**: Implement client-side caching for common requests
5. **Worker Processes**: Adjust `API_WORKERS` for your server capacity

---

### Deployment

#### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV HF_API_KEY=${HF_API_KEY}
ENV API_HOST=0.0.0.0
ENV API_WORKERS=4

CMD ["python", "backend.py"]
```

```bash
# Build
docker build -t multi-modal-agent .

# Run
docker run -e HF_API_KEY="your-key" -p 8000:8000 multi-modal-agent
```

#### Systemd Service (Linux)

Create `/etc/systemd/system/multi-modal-agent.service`:

```ini
[Unit]
Description=Multi-Modal Agent API
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/path/to/app
Environment="HF_API_KEY=your-key"
Environment="API_PORT=8000"
ExecStart=/usr/bin/python3 /path/to/app/backend.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable multi-modal-agent
systemctl start multi-modal-agent
systemctl status multi-modal-agent
```

---

### Monitoring & Logging

#### Enable Debug Logging

Set `DEBUG=True` environment variable to see detailed logs.

#### Access Logs

The API logs all requests with timestamps, response codes, and processing time.

```
2024-04-11 10:30:45 - backend - INFO - Processing request: text=..., image=no, verbose=True
2024-04-11 10:30:50 - backend - INFO - Workflow completed successfully: task=summary
```

#### Health Monitoring

```bash
# Check health every 30 seconds
watch -n 30 'curl -s http://localhost:8000/health | jq'
```

---

### Troubleshooting

#### API won't start
1. Check `HF_API_KEY` is set: `echo $HF_API_KEY`
2. Check port isn't in use: `lsof -i :8000`
3. Check Python version: `python --version` (requires 3.10+)

#### Slow responses
1. Increase `HF_MODEL_LOADING_TIMEOUT`
2. Reduce batch size
3. Check HF API status
4. Consider caching responses

#### Out of memory
1. Reduce `API_WORKERS`
2. Implement request queuing
3. Add swap space
4. Use smaller models

#### CORS errors (frontend)
1. CORS is enabled by default for all origins
2. For production, update `allow_origins` in `create_app()`

---

### API Testing

Run the included test suite:

```bash
python backend_example.py
```

This demonstrates all endpoints and error cases.

---

### Advanced Features

#### Custom Workflow Behavior

Modify `backend.py` to customize response handling:

```python
@app.post("/process")
async def process(text: str = Form(...)):
    # Custom pre-processing
    text = text.lower()
    
    # Execute
    final_state = run_workflow(...)
    
    # Custom post-processing
    if final_state.task_type == TaskType.SUMMARIZATION:
        # Add custom logic
        pass
    
    return ProcessResponse(...)
```

#### Custom Task Routes

Add new task types to the workflow:

```python
# In workflow.py
def node_custom_task(state, agent):
    # Custom node implementation
    pass

# In create_app()
workflow.add_node("custom", node_custom_task)
workflow.add_conditional_edges(...)
```

---

### Support & Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **GitHub**: Your repository
- **Issues**: Report bugs at GitHub Issues

---
"""

if __name__ == "__main__":
    # This file is documentation. Run the backend with:
    # python backend.py
    print(__doc__)
