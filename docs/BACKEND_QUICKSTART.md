"""
FastAPI Backend - Quick Start Guide

Get the API running in 3 steps.
"""

# ============================================================================
# QUICK START - Run in 3 Steps
# ============================================================================

"""
## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages including:
- FastAPI (REST framework)
- Uvicorn (ASGI server)
- Pydantic (request/response validation)
- All agent and workflow dependencies

---

## Step 2: Set Environment Variable

```bash
# REQUIRED - Your HuggingFace Inference API key
export HF_API_KEY="hf_your_api_key_here"

# Optional - Customize these as needed
export DEBUG="False"
export API_HOST="0.0.0.0"
export API_PORT="8000"
export HF_TIMEOUT="30"
export HF_MAX_RETRIES="3"
```

### Getting HuggingFace API Key

1. Go to https://huggingface.co/settings/tokens
2. Create new token (or use existing one)
3. Copy the token value
4. Set as environment variable (see above)

---

## Step 3: Run the Server

```bash
python backend.py
```

You should see:
```
2024-04-11 10:00:00 - backend - INFO - Starting Multi-Modal Agent API
2024-04-11 10:00:01 - backend - INFO - Building LangGraph workflow...
2024-04-11 10:00:05 - backend - INFO - ✓ Workflow initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ API is Ready!

### Access Points

- **API**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Test It Out

### Using curl

```bash
# Simple text processing (summarization by default)
curl -X POST http://localhost:8000/process \\
  -F "text=Artificial Intelligence is transforming industries..." 

# With verbose logging
curl -X POST http://localhost:8000/process \\
  -F "text=Tell me about AI" \\
  -F "verbose=true"

# With image analysis
curl -X POST http://localhost:8000/process \\
  -F "text=Analyze this image" \\
  -F "image=@path/to/image.jpg"

# Image generation with download
curl -X POST http://localhost:8000/process-and-download \\
  -F "text=A serene sunset" \\
  -o generated_image.png
```

### Using Python

```python
import requests

# Test 1: Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Test 2: Text processing
response = requests.post(
    "http://localhost:8000/process",
    data={"text": "Tell me about AI", "verbose": True}
)
result = response.json()
print(f"Task: {result['task_type']}")
print(f"Success: {result['success']}")
if result['result']:
    print(f"Result: {result['result']['content'][:100]}...")

# Test 3: Batch processing
response = requests.post(
    "http://localhost:8000/process-batch",
    data={"texts": ["Summarize this", "What's the sentiment?", "Generate an image"]}
)
result = response.json()
print(f"Processed: {result['successful']}/{result['total']}")

# Test 4: Image generation
response = requests.post(
    "http://localhost:8000/process-and-download",
    data={"text": "A mountain landscape at sunset"}
)
if 'image' in response.headers.get('content-type', ''):
    with open('image.png', 'wb') as f:
        f.write(response.content)
    print("Image downloaded!")
```

### Run Full Test Suite

```bash
python backend_example.py
```

This runs 8 comprehensive examples demonstrating all endpoints.

---

## What the API Does

The FastAPI backend provides HTTP endpoints for the multi-modal agent workflow:

**Endpoints:**

1. **GET /health** - Check API status
2. **GET /** - API information
3. **POST /process** - Main endpoint (text + optional image)
4. **POST /process-and-download** - Image generation with binary download
5. **POST /process-batch** - Batch process multiple texts

**Task Auto-Detection:**

Based on input, automatically routes to:
- **SUMMARIZATION** - Keywords: summarize, summary, condense
- **STANCE_DETECTION** - Keywords: opinion, sentiment, believe
- **IMAGE_GENERATION** - Keywords: generate, create, draw
- **IMAGE_ANALYSIS** - If image provided OR keywords: analyze, describe

---

## Configuration

### Environment Variables

```
HF_API_KEY              [REQUIRED] HuggingFace API key
HF_TIMEOUT              Request timeout (default: 30s)
HF_MAX_RETRIES          Retry attempts (default: 3)
HF_MODEL_LOADING_TIMEOUT Model loading timeout (default: 120s)

API_HOST                Server host (default: 0.0.0.0)
API_PORT                Server port (default: 8000)
API_RELOAD              Enable auto-reload (default: False)
API_WORKERS             Worker processes (default: 4)

DEBUG                   Enable debug logging (default: False)
MAX_IMAGE_SIZE          Max upload size (default: 50MB)
MAX_BATCH_SIZE          Max batch size (default: 100)
```

### File Configuration

Edit `config.py` to customize defaults or add new settings.

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'fastapi'"**
- Run: `pip install -r requirements.txt`

**"HF_API_KEY environment variable is required"**
- Set: `export HF_API_KEY="your-key"`
- Or: Verify it's actually set with `echo $HF_API_KEY`

**"Address already in use"**
- Change port: `export API_PORT=8001`
- Or: Kill other process on port 8000

**"Workflow not initialized"**
- Wait 5-10 seconds for startup (models loading)
- Check logs for errors
- Verify HF_API_KEY is valid

**Slow responses**
- Increase timeouts: `export HF_TIMEOUT=60`
- Check HuggingFace API status
- First request is slower (model loading)

---

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t multi-modal-agent-api .

# Run container (requires HF_API_KEY)
docker run \\
  -e HF_API_KEY="your-key" \\
  -p 8000:8000 \\
  multi-modal-agent-api
```

### Using Gunicorn

```bash
pip install gunicorn

gunicorn backend:app \\
  --workers 4 \\
  --worker-class uvicorn.workers.UvicornWorker \\
  --bind 0.0.0.0:8000
```

### Using systemd (Linux)

1. Create service file at `/etc/systemd/system/multi-modal-api.service`
2. See BACKEND_API.md for complete systemd configuration
3. Run: `systemctl start multi-modal-api`

---

## Next Steps

1. **Integrate with Frontend** - Connect to Streamlit or React app
2. **Add Authentication** - Use API keys or JWT tokens
3. **Enable Caching** - Cache common responses
4. **Set up Monitoring** - Log metrics and errors
5. **Auto-scaling** - Deploy multiple instances with load balancer

---

## Documentation

- **Full API Docs**: See `BACKEND_API.md` for comprehensive documentation
- **Examples**: See `backend_example.py` for all usage examples
- **Code**: See `backend.py` for implementation details
- **Swagger**: http://localhost:8000/docs (interactive)
- **ReDoc**: http://localhost:8000/redoc (alternative format)

---

## Tips & Tricks

### Verbose Logging

Enable detailed execution trace:
```bash
curl -X POST http://localhost:8000/process \\
  -F "text=Summarize this" \\
  -F "verbose=true"
```

### Batch Processing

Process multiple items efficiently:
```python
texts = ["Text 1", "Text 2", ..., "Text 100"]
response = requests.post(
    "http://localhost:8000/process-batch",
    data={"texts": texts}
)
```

### Rate Limiting

Add via middleware or API gateway:
- nginx (reverse proxy)
- CloudFlare
- AWS API Gateway
- Custom FastAPI middleware

### Caching

Implement with Redis or SQLite:
- Cache common summarizations
- Cache image analyses
- Cache frequently generated images

---

## Support

- **Issues**: Debug using verbose mode and check logs
- **Logs**: Check console output for detailed error messages
- **Health**: Use `/health` endpoint to monitor status
- **Docs**: Interactive documentation at /docs

---

## What's Next?

✅ Backend API is running!

Next steps:
1. Test all endpoints at http://localhost:8000/docs
2. Run examples with `python backend_example.py`
3. Integrate with frontend application
4. Deploy to production (Docker/systemd)
5. Set up monitoring and logging

---
"""

if __name__ == "__main__":
    print(__doc__)
