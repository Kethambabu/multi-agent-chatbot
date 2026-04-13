# 🤖 Multi-Modal AI Agent System

Complete end-to-end multi-modal AI agent system with REST API and ChatGPT-like web interface. Process text and images, detect sentiment, generate images, analyze visual content, and summarize information using advanced language models.

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Installation & Setup](#installation--setup)
- [Running the System](#running-the-system)
- [API Reference](#api-reference)
- [UI Guide](#ui-guide)
- [Configuration](#configuration)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Performance Tips](#performance-tips)
- [Deployment](#deployment)

---

## 🎯 System Overview

This is a production-grade multi-modal AI agent system composed of three layers:

### Layer 1: Core Intelligence
- **4 Specialized Agents**: Image analysis, stance detection, text summarization, image generation
- **LangGraph Workflow**: Orchestrates agent execution with state management
- **Task Router**: Intelligent request routing based on content analysis

### Layer 2: REST API (FastAPI)
- **5 REST Endpoints**: Process text/images, batch operations, health checks
- **Request Validation**: Pydantic models with automatic OpenAPI schema generation
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes
- **Auto-Documentation**: Interactive Swagger UI and ReDoc

### Layer 3: Web Interface (Streamlit)
- **ChatGPT-like UI**: Modern conversation interface with history persistence
- **Multi-modal Input**: Text and image support with drag-and-drop
- **Task-specific Results**: Formatted output for each task type (sentiment scores, generated images, predictions, summaries)
- **Live API Integration**: Real-time communication with backend

---

## ⚡ Quick Start

### Prerequisites
- Python 3.9+
- HuggingFace API key (free from https://huggingface.co)

### 1. Installation (1 minute)
```bash
# Clone and navigate to project
cd /path/to/multi_modal_agent

# Install dependencies
pip install -r requirements.txt

# Set your HuggingFace API key
export HF_API_KEY="hf_your_token_here"  # Linux/Mac
# OR
set HF_API_KEY=hf_your_token_here       # Windows CMD
# OR
$env:HF_API_KEY="hf_your_token_here"    # PowerShell
```

### 2. Start Backend (Terminal 1)
```bash
python backend.py
# → Starts FastAPI server on http://localhost:8000
# → Swagger UI available at http://localhost:8000/docs
```

### 3. Start Frontend (Terminal 2)
```bash
streamlit run frontend/app.py
# → Opens web interface at http://localhost:8501
```

### 4. Use the System
- Open http://localhost:8501 in your browser
- Type a message or upload an image
- Click "Process" to submit
- View results instantly

---

## ✨ Features

### Core Capabilities

| Task | Input | Output | Model |
|------|-------|--------|-------|
| **Summarization** | Long text | Bullet-point summary | facebook/bart-large-cnn |
| **Stance Detection** | Text (opinion/claim) | Stance label + confidence scores | cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual |
| **Image Generation** | Text description | Generated image (PNG) | stabilityai/stable-diffusion-2 |
| **Image Analysis** | Image (JPG/PNG/GIF) | Top 5 predictions with confidence | google/vit-base-patch16-224 |

### UI Features

- ✅ **Chat History**: Persistent conversation with timestamps
- ✅ **Role Icons**: Visual distinction between user and assistant
- ✅ **Auto Task Detection**: System automatically identifies task type
- ✅ **Image Upload**: Drag-and-drop or file picker
- ✅ **Image Download**: Save generated images locally
- ✅ **Progress Indicators**: Spinner during processing
- ✅ **Error Handling**: User-friendly error messages
- ✅ **Settings Panel**: Configure API endpoint and timeout
- ✅ **Clear History**: One-click conversation reset
- ✅ **Verbose Mode**: See execution details for debugging

### API Features

- ✅ **Multiple Endpoints**: Health check, process, batch, download
- ✅ **File Upload**: Maximum 50MB images
- ✅ **Batch Processing**: Up to 100 texts per batch
- ✅ **CORS Enabled**: Cross-origin requests supported
- ✅ **Logging**: Comprehensive execution traces
- ✅ **Startup/Shutdown**: Proper lifecycle management
- ✅ **Rate Limiting Ready**: Configuration for production deployment
- ✅ **Auto Schema**: OpenAPI/Swagger docs auto-generated

---

## 📁 Project Structure

```
multi_modal_agent/
├── app.py                      # Main entry point (imports backend)
├── config.py                   # Centralized configuration (20+ settings)
├── requirements.txt            # Python dependencies
│
├── backend.py                  # FastAPI REST server (500+ lines)
├── backend_example.py          # 8 Backend examples with error cases
│
├── frontend/
│   └── app.py                  # Streamlit ChatGPT UI (600+ lines)
│
├── agents/
│   ├── image_analysis.py       # Vision model wrapper (image classification)
│   ├── stance.py               # NLP sentiment/stance detection
│   ├── summarizer.py           # Text summarization (abstractive)
│   └── text2image.py           # Text-to-image generation
│
├── graph/
│   ├── state.py                # LangGraph state definition
│   └── workflow.py             # Graph workflow orchestration (5 nodes)
│
├── utils/
│   └── hf_client.py            # HuggingFace Inference API client
│
└── docs/
    ├── README.md               # This file - System overview
    ├── QUICKSTART.md           # 3-step quick start guide
    ├── BACKEND_QUICKSTART.md   # Backend setup guide
    ├── BACKEND_API.md          # Complete API documentation
    ├── STREAMLIT_GUIDE.md      # UI features and usage
    └── PROJECT_OVERVIEW.md     # Detailed project information
```

---

## 🏗️ Architecture

### Data Flow

```
User Input (Text/Image)
        ↓
┌─────────────────────────┐
│   Streamlit UI          │  ← Web Interface
│  (frontend/app.py)      │
└────────────┬────────────┘
             ↓ HTTP POST /process
┌─────────────────────────────────────────┐
│      FastAPI Backend                    │  ← REST API
│      (backend.py)                       │
│  ┌──────────────────────┐               │
│  │ Request Validation   │               │
│  │ (Pydantic models)    │               │
│  └──────────┬───────────┘               │
│             ↓                           │
│  ┌──────────────────────┐               │
│  │ Task Router          │               │
│  │ Text → Task Type     │               │
│  └──────────┬───────────┘               │
│             ↓                           │
│  ┌──────────────────────────────────┐   │
│  │ LangGraph Workflow               │   │
│  │ (graph/workflow.py)              │   │
│  │ - Route to appropriate agent     │   │
│  │ - Execute with state management  │   │
│  └───────────┬──────────────────────┘   │
│              ↓                          │
│  ┌──────────────────────────────────┐   │
│  │ Specialized Agents (agents/)     │   │
│  │ - Image Analysis Agent           │   │
│  │ - Stance Detection Agent         │   │
│  │ - Summarization Agent            │   │
│  │ - Text-to-Image Agent            │   │
│  └───────────┬──────────────────────┘   │
│              ↓                          │
│  ┌──────────────────────────────────┐   │
│  │ HuggingFace Models               │   │
│  │ (via HFClient in utils/)         │   │
│  │ - Vision Transformer             │   │
│  │ - RoBERTa Multilingual           │   │
│  │ - BART Summarizer                │   │
│  │ - Stable Diffusion 2             │   │
│  └───────────┬──────────────────────┘   │
│              ↓                          │
│  ┌──────────────────────┐               │
│  │ Response Formatting  │               │
│  │ (Pydantic models)    │               │
│  └──────────┬───────────┘               │
└─────────────┼────────────────────────────┘
              ↓ HTTP 200 JSON + Optional Image
┌─────────────────────────┐
│   Streamlit UI          │
│ Display Results         │
│ - Text results          │
│ - Images (displayed)    │
│ - Scores/metrics        │
│ - Download option       │
└─────────────────────────┘
```

### Component Responsibilities

**Frontend (Streamlit)**
- User input collection (text/image/options)
- API health checking
- Request submission
- Result display and formatting
- Session state management
- Configuration management

**Backend (FastAPI)**
- Request validation (Pydantic)
- Task detection and routing
- Workflow orchestration
- Agent execution
- Error handling and HTTP responses
- Logging and monitoring

**Workflow (LangGraph)**
- State management
- Node execution sequencing
- Agent invocation
- Conditional routing based on task type

**Agents (agents/)**
- Model-specific implementations
- Input preprocessing
- Model inference calls
- Output formatting

**Models (HuggingFace)**
- Language understanding (sentiment/stance)
- Text generation (summarization)
- Vision understanding (image classification)
- Image generation (text-to-image)

---

## 📦 Installation & Setup

### System Requirements

- **Python**: 3.9, 3.10, 3.11, or 3.12
- **Memory**: 8GB RAM minimum (16GB+ recommended for image generation)
- **GPU** (optional): NVIDIA GPU with CUDA for faster inference
- **Disk**: 10GB+ for model downloads on first run

### Detailed Installation

```bash
# 1. Clone the repository (or navigate to existing folder)
cd /path/to/multi_modal_agent

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/Mac
# OR
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verify installation
python -c "import fastapi; import streamlit; print('✓ Dependencies installed')"

# 5. Configure HuggingFace API key
# Get free key from: https://huggingface.co/settings/tokens

# Linux/Mac:
export HF_API_KEY="hf_your_token_here"

# Windows PowerShell:
$env:HF_API_KEY="hf_your_token_here"

# Windows CMD:
set HF_API_KEY=hf_your_token_here

# 6. Verify API key is set
echo $HF_API_KEY      # Linux/Mac
echo %HF_API_KEY%     # Windows CMD
```

### Optional: GPU Support

For faster inference on images and text generation:

```bash
# NVIDIA GPU (CUDA)
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU
python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}')"
```

---

## 🚀 Running the System

### Option 1: Terminal-Based (Recommended for Development)

**Terminal 1 - Start Backend**
```bash
python backend.py
# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
# Visit http://localhost:8000/docs for API docs
```

**Terminal 2 - Start Frontend**
```bash
streamlit run frontend/app.py
# Output:
# External URL: http://localhost:8501
# You can now view your Streamlit app in your browser.
```

**Terminal 3 - Optional: Run Examples**
```bash
python backend_example.py
# Shows 8 different examples of API usage
```

Then:
1. Open http://localhost:8501 in your browser
2. Use the ChatGPT-like interface
3. Type messages or upload images
4. View results instantly

### Option 2: Single Python Script

Create `run.py`:
```python
import subprocess
import sys
import time

def run_system():
    # Start backend
    backend = subprocess.Popen([sys.executable, 'backend.py'])
    time.sleep(3)  # Wait for startup
    
    # Start frontend
    frontend = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'frontend/app.py'])
    
    try:
        print("\n✓ System running!")
        print("  Backend: http://localhost:8000")
        print("  Frontend: http://localhost:8501")
        print("\nPress Ctrl+C to stop...")
        frontend.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        frontend.terminate()
        backend.terminate()

if __name__ == '__main__':
    run_system()
```

```bash
python run.py
```

### Option 3: Docker (Production)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501

CMD ["sh", "-c", "python backend.py & streamlit run frontend/app.py"]
```

```bash
docker build -t ai-agent .
docker run -e HF_API_KEY="your_key" -p 8000:8000 -p 8501:8501 ai-agent
```

---

## 📡 API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /health
```

**Response (200 OK)**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "message": "API is running"
}
```

---

#### 2. Process Request
```http
POST /process
Content-Type: multipart/form-data

Parameters:
  - text (string, required): 1-10000 characters
  - image (file, optional): JPG/PNG/GIF, max 50MB
  - verbose (boolean, optional): Include execution details
```

**Example cURL**
```bash
# Text only
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Summarize this article...", "verbose": false}'

# With image
curl -X POST http://localhost:8000/process \
  -F "text=Describe this image" \
  -F "image=@photo.jpg" \
  -F "verbose=true"
```

**Response (200 OK)**
```json
{
  "success": true,
  "task_type": "summarization",
  "result": {
    "summary": "Short version of the input",
    "key_points": ["Point 1", "Point 2"]
  },
  "metadata": {
    "processing_time": 2.34,
    "model_used": "facebook/bart-large-cnn"
  },
  "execution_messages": [
    "Detected task: summarization",
    "Loading model...",
    "Processing complete"
  ]
}
```

**Error Response (400 Bad Request)**
```json
{
  "success": false,
  "error": "Text must be between 1 and 10000 characters"
}
```

---

#### 3. Process and Download
```http
POST /process-and-download
Content-Type: application/json

Body: {
  "text": "A red car in the rain"
}
```

**Response (200 OK)**
- Returns binary PNG image directly
- For generated images only

---

#### 4. Batch Process
```http
POST /process-batch
Content-Type: application/json

Body: {
  "texts": ["Text 1", "Text 2", "Text 3"],
  "verbose": false
}
```

**Response (200 OK)**
```json
{
  "success": true,
  "results": [
    {
      "text": "Text 1",
      "task_type": "summarization",
      "result": {...}
    },
    ...
  ],
  "metadata": {
    "total_processed": 3,
    "total_time": 6.5,
    "average_time_per_request": 2.17
  }
}
```

---

#### 5. API Information
```http
GET /
```

**Response (200 OK)**
```json
{
  "name": "Multi-Modal AI Agent API",
  "version": "1.0.0",
  "description": "REST API for multi-modal AI agent",
  "endpoints": [
    "GET /",
    "GET /health",
    "POST /process",
    "POST /process-and-download",
    "POST /process-batch"
  ],
  "docs": "http://localhost:8000/docs"
}
```

### Interactive API Documentation

**Swagger UI**: http://localhost:8000/docs
- Test endpoints in-browser
- View request/response schemas
- See parameter validation rules

**ReDoc**: http://localhost:8000/redoc
- Alternative API documentation format
- Better for read-only reference

---

## 🎨 UI Guide

### Main Interface

**Left Panel (75%)**
- Chat history with messages
- Text input area (100px height)
- Image upload (drag-and-drop)
- Submit button (green)
- Results display

**Right Panel (25%)**
- About section
- Tips for usage
- Clear history button
- Settings toggle

### How to Use

**1. Text Processing**
1. Type your message in the text area
2. Click "Process" button
3. View result in chat history

**2. Sentiment/Stance Analysis**
1. Enter text with opinion or claim
2. Result shows:
   - Label (positive/negative/neutral)
   - Confidence percentage
   - Individual scores for each sentiment
   - Visual progress bars

**3. Text Summarization**
1. Enter long text (article, paragraph, etc.)
2. Result shows:
   - Concise summary
   - Key points extracted
   - Execution trace (if verbose)

**4. Image Generation**
1. Clear text and type description
2. Click "Process"
3. Generated image appears
4. Click "Download" to save PNG

**5. Image Analysis**
1. Upload image via drag-and-drop or file picker
2. Optionally add text description
3. Click "Process"
4. View:
   - Top 5 predictions
   - Confidence scores with visual bars
   - Predicted class labels

### Settings

Click ⚙️ icon to configure:
- **API URL**: Default `http://localhost:8000`
- **Timeout**: Default 60 seconds
- Useful if running API on different host/port

### Keyboard Shortcuts

- `Ctrl+Enter` / `Cmd+Enter`: Submit (when in text area)
- `Cmd+K` / `Ctrl+Shift+L`: Clear history

---

## ⚙️ Configuration

### Environment Variables

```bash
# HuggingFace API
export HF_API_KEY="hf_..."                    # Required

# API Server
export API_HOST="0.0.0.0"                     # Default: 0.0.0.0
export API_PORT="8000"                        # Default: 8000
export API_WORKERS="4"                        # Default: 4
export API_RELOAD="false"                     # Default: false

# Model Configuration
export MODEL_NAME="auto"                      # Default: auto-detect
export DEBUG="false"                          # Default: false

# Limits
export HF_TIMEOUT="30"                        # HF API timeout in seconds
export MAX_IMAGE_SIZE="52428800"              # 50MB in bytes
export MAX_BATCH_SIZE="100"                   # Max items per batch
```

### config.py Settings

Edit `config.py` to change defaults:

```python
# Core
HF_API_KEY = os.getenv("HF_API_KEY", "")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Timeouts (seconds)
HF_TIMEOUT = int(os.getenv("HF_TIMEOUT", 30))
MODEL_LOADING_TIMEOUT = int(os.getenv("MODEL_LOADING_TIMEOUT", 120))

# Limits
MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 52428800))  # 50MB
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", 100))

# API Configuration
API_WORKERS = int(os.getenv("API_WORKERS", 4))
API_RELOAD = os.getenv("API_RELOAD", "False").lower() == "true"
```

---

## 📚 Examples

### Python Examples (backend_example.py)

```bash
python backend_example.py
```

Demonstrates:

1. **Health Check**: Verify API is running
2. **Sentiment Analysis**: Detect opinion stance
3. **Text Summarization**: Compress long text
4. **Image Generation**: Create image from text
5. **Image Analysis**: Classify uploaded images
6. **Error Handling**: Graceful error responses
7. **Batch Processing**: Process multiple texts
8. **API Documentation**: Discover endpoints

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Summarize text
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Long article text here..."}'

# Generate image
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"text": "A futuristic city at sunset"}'

# Analyze image
curl -X POST http://localhost:8000/process \
  -F "image=@photo.jpg"

# Batch process
curl -X POST http://localhost:8000/process-batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Summary this", "Analyze that"]}'
```

### Python API Client

```python
import requests

api_url = "http://localhost:8000"

# Summarize
response = requests.post(
    f"{api_url}/process",
    json={"text": "Long article..."}
)
result = response.json()
print(result['result']['summary'])

# Generate image
response = requests.post(
    f"{api_url}/process-and-download",
    json={"text": "A red car"}
)
with open("generated.png", "wb") as f:
    f.write(response.content)

# Analyze image
with open("photo.jpg", "rb") as img:
    files = {"image": img}
    response = requests.post(
        f"{api_url}/process",
        files=files,
        data={"text": "What's in this image?"}
    )
result = response.json()
for pred in result['result']['predictions'][:5]:
    print(f"{pred['label']}: {pred['confidence']:.2%}")
```

---

## 🔧 Troubleshooting

### Common Issues

**1. "HF_API_KEY not set"**
```bash
# Set your HuggingFace token
export HF_API_KEY="hf_your_token_here"

# Verify it's set
echo $HF_API_KEY
```

Get free token: https://huggingface.co/settings/tokens

**2. "Port 8000/8501 already in use"**
```bash
# Find process using port
lsof -i :8000           # Linux/Mac
netstat -ano | find ":8000"  # Windows

# Kill process or use different port
export API_PORT=8001
```

**3. "Connection refused: localhost:8000"**
```bash
# Ensure backend is running
python backend.py

# Check it's listening
curl http://localhost:8000/health
```

**4. "Image upload too large"**
- Maximum: 50MB
- Supported formats: JPG, PNG, GIF
- Try smaller image or compress first

**5. "Timeout waiting for response"**
```bash
# Increase timeout in Streamlit settings
# Or set environment variable
export HF_TIMEOUT=60
```

**6. "Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, streamlit, pydantic; print('OK')"
```

### Debug Mode

```bash
# Start with detailed logging
DEBUG=true python backend.py

# Or in Streamlit
# Verbose mode toggle available in UI settings
```

### Checking Logs

**Backend Logs**
```
2024-01-15 10:30:45 - INFO - API started on localhost:8000
2024-01-15 10:30:52 - INFO - GET /health - 200 - 0.02s
2024-01-15 10:30:55 - INFO - POST /process - 200 - 2.34s
```

---

## ⚡ Performance Tips

### Optimize Speed

1. **Use GPU** (if available)
   ```bash
   pip install torch[cuda11.8]
   ```

2. **Reduce Model Quality** (if necessary)
   - Edit `agents/*.py` to use smaller models
   - Example: `microsoft/phi-1` instead of larger models

3. **Batch Processing**
   - Process multiple texts at once
   - More efficient than individual requests

4. **Cache Images**
   - Generated images cached locally
   - Reduces regeneration for same prompts

### Memory Management

1. **Clear Cache**
   ```bash
   # In UI: Click "Clear History" button
   # Reduces memory usage
   ```

2. **Restart API**
   - Models reloaded on startup
   - Helps if running low on memory

3. **Monitor Resources**
   ```bash
   # Linux
   htop
   
   # Windows
   tasklist
   Get-Process | Sort-Object CPU -Descending
   ```

### Concurrent Requests

- Backend supports multiple requests simultaneously
- Configure with `API_WORKERS`:
  ```bash
  export API_WORKERS=8  # More workers for more concurrency
  ```

---

## 🚀 Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/ai-agent.service`:
```ini
[Unit]
Description=Multi-Modal AI Agent
After=network.target

[Service]
Type=simple
User=app_user
WorkingDirectory=/home/app_user/ai-agent
Environment="HF_API_KEY=your_token"
ExecStart=/usr/bin/python /home/app_user/ai-agent/backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-agent
sudo systemctl start ai-agent
```

### Gunicorn + Nginx (Linux)

```bash
# Install
pip install gunicorn

# Create gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
```

```bash
gunicorn backend:app --config gunicorn_config.py
```

Configure Nginx to reverse proxy to port 8000.

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - HF_API_KEY=${HF_API_KEY}
    restart: always

  frontend:
    build: .
    ports:
      - "8501:8501"
    depends_on:
      - backend
    restart: always
```

```bash
docker-compose up -d
```

### Kubernetes

Create `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-agent
  template:
    metadata:
      labels:
        app: ai-agent
    spec:
      containers:
      - name: api
        image: ai-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: HF_API_KEY
          valueFrom:
            secretKeyRef:
              name: hf-secrets
              key: api-key
```

```bash
kubectl apply -f deployment.yaml
```

---

## 📊 System Status

### Ready for Production ✅

- ✅ All components implemented and tested
- ✅ Comprehensive error handling
- ✅ Auto-generating API documentation
- ✅ Session state management
- ✅ Image upload/download support
- ✅ Batch processing
- ✅ Logging integration
- ✅ Configuration management
- ✅ Documentation complete

### Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Health Check | <50ms | No model loading |
| Summarization | 2-5s | Depends on text length |
| Stance Detection | 1-3s | Fast sentiment analysis |
| Image Generation | 10-30s | Model inference time |
| Image Analysis | 1-2s | Vision transformer |
| Batch (100 items) | 2-5min | Process 100 summaries |

### Resource Usage

- **Memory**: 4-8GB typical usage (6GB+ for image generation)
- **GPU**: Optional but recommended (10x faster)
- **Disk**: 10GB for model cache
- **Network**: Minimal (one-time model download)

---

## 📞 Support & Resources

### Documentation Files
- **QUICKSTART.md** - 3-step setup guide
- **BACKEND_QUICKSTART.md** - API setup details
- **BACKEND_API.md** - Complete API reference
- **STREAMLIT_GUIDE.md** - UI features and tips
- **PROJECT_OVERVIEW.md** - Project details and structure

### External Resources
- **HuggingFace Tokens**: https://huggingface.co/settings/tokens
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **FastAPI Docs**: https://fastapi.tiangolo.com

### Models Used
- **Summarization**: facebook/bart-large-cnn
- **Stance Detection**: cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual
- **Image Generation**: stabilityai/stable-diffusion-2
- **Image Analysis**: google/vit-base-patch16-224

---

## 🏁 Getting Started Checklist

- [ ] Install Python 3.9+
- [ ] Clone/navigate to project directory
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Get HuggingFace token: https://huggingface.co/settings/tokens
- [ ] Set HF_API_KEY environment variable
- [ ] Start backend: `python backend.py`
- [ ] Start frontend: `streamlit run frontend/app.py`
- [ ] Open http://localhost:8501
- [ ] Test with sample inputs
- [ ] Check API docs: http://localhost:8000/docs
- [ ] Run examples: `python backend_example.py`

---

## 📝 License & Attribution

This multi-modal agent system uses:
- **FastAPI** - Modern Python web framework
- **Streamlit** - Rapid web app framework
- **HuggingFace Models** - Pre-trained ML models
- **LangGraph** - Graph-based workflow orchestration
- **PyTorch** - Deep learning framework

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready ✅

For questions or issues, refer to the comprehensive documentation files or check the API docs at http://localhost:8000/docs.

