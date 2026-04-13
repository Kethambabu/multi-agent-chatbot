"""
Quick Start - Run Everything

3 terminals to get the complete system running.
"""

# ============================================================================
# COMPLETE SYSTEM - QUICK START
# ============================================================================

"""
## Multi-Modal Agent - Complete System Setup

Run all components and test the full system.

---

### Prerequisites

1. Python 3.10+
2. HuggingFace API key
3. Dependencies installed

```bash
pip install -r requirements.txt
```

---

### Setup (One Time)

Set environment variables:

**Linux/macOS:**
```bash
export HF_API_KEY="your-huggingface-api-key"
export DEBUG="False"
export API_PORT="8000"
```

**Windows (PowerShell):**
```powershell
$env:HF_API_KEY="your-huggingface-api-key"
$env:DEBUG="False"
$env:API_PORT="8000"
```

---

### Running the System

#### Option 1: Three Terminals (Recommended)

**Terminal 1 - Backend API:**
```bash
python backend.py
# Should show: INFO: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Streamlit UI:**
```bash
streamlit run frontend/app.py
# Should show: You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
```

**Terminal 3 - (Optional) Test Examples:**
```bash
python backend_example.py
# Runs all 8 endpoint examples
```

---

#### Option 2: Single Terminal with Python Subprocess

Create `run_all.py`:

```python
import subprocess
import time
import os

os.environ["HF_API_KEY"] = "your-key"

# Start backend
backend_process = subprocess.Popen(
    ["python", "backend.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for backend to start
time.sleep(5)

# Start frontend
streamlit_process = subprocess.Popen(
    ["streamlit", "run", "frontend/app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

try:
    # Keep running until interrupted
    backend_process.wait()
    streamlit_process.wait()
except KeyboardInterrupt:
    backend_process.terminate()
    streamlit_process.terminate()
```

Run with:
```bash
python run_all.py
```

---

### Access Points

Once running:

- **Streamlit UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

### First Run Checklist

- [ ] Backend running (see "Uvicorn running" message)
- [ ] Streamlit running (see "Streamlit app running" message)
- [ ] Browser opened to http://localhost:8501
- [ ] API status shows "✓ API Connected"
- [ ] Try sending a text: "Summarize this about AI"
- [ ] See results appear below

---

### Testing the System

#### Test 1: Text Summarization

1. Open UI: http://localhost:8501
2. Type: "Artificial Intelligence is transforming industries. When combined with machine learning, AI can process vast amounts of data. The future of AI is promising."
3. Click "📤 Submit"
4. Should see summary in ~10 seconds

#### Test 2: Sentiment Analysis

1. Type: "I absolutely love this product!"
2. Click "📤 Submit"
3. Should see sentiment: "positive" with ~99% confidence

#### Test 3: Image Generation

1. Type: "A serene mountain landscape at sunset"
2. Click "📤 Submit"
3. Should see generated image in ~30-60 seconds
4. Can download with "📥 Download Image" button

#### Test 4: Image Analysis

1. Prepare or download a test image
2. Upload image in UI
3. Type: "What's in this image?"
4. Click "📤 Submit"
5. Should see top 5 predictions with confidence scores

---

### File Structure Summary

```
multi_modal_agent/
├── backend.py             # FastAPI REST API
├── frontend/app.py        # Streamlit UI
├── config.py              # Configuration
├── requirements.txt       # Dependencies
│
├── agents/                # 4 specialized agents
├── graph/                 # LangGraph workflow
├── utils/                 # HF API client
│
├── BACKEND_QUICKSTART.md  # Backend setup (3 steps)
├── BACKEND_API.md         # API documentation
├── STREAMLIT_GUIDE.md     # Frontend guide
└── PROJECT_OVERVIEW.md    # Complete overview
```

---

### Troubleshooting

#### Backend won't start

```bash
# Check port is free
lsof -i :8000

# Kill existing process
kill -9 <PID>

# Try different port
export API_PORT=8001
python backend.py
```

#### Streamlit won't connect to API

```bash
# Check API is running
curl http://localhost:8000/health

# In Streamlit UI, click ⚙️ Settings
# Verify API URL is: http://localhost:8000
# Click "Test Connection"
```

#### Model loading timeout

```bash
# First request loads models (can take 30-120 seconds)
# This is normal - just wait

# Or increase timeout:
# In Streamlit UI ⚙️ Settings
# Set timeout to 120+ seconds
```

#### Memory issues

```bash
# If running low on memory:
# - Close other applications
# - Use smaller batch size (1 item at a time)
# - Restart backend to clear memory
```

---

### Performance Notes

**First Request (One Time)**:
- Load time: 30-120 seconds (models loading)
- This is normal - HuggingFace models are large
- Subsequent requests: 3-15 seconds

**Typical Times by Task**:
- Summarization: 5-15 seconds
- Sentiment: 2-5 seconds
- Image Generation: 30-60 seconds
- Image Analysis: 3-8 seconds

---

### Production Deployment

To deploy to production:

#### Option 1: Docker Compose

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
      - API_HOST=0.0.0.0
    command: python backend.py

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    depends_on:
      - backend
    environment:
      - API_URL=http://backend:8000
    command: streamlit run frontend/app.py --server.port=8501
```

```bash
export HF_API_KEY="your-key"
docker-compose up
```

#### Option 2: systemd Services

Create `/etc/systemd/system/multi-modal-backend.service`:

```ini
[Unit]
Description=Multi-Modal Agent Backend
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/path/to/app
Environment="HF_API_KEY=your-key"
ExecStart=/usr/bin/python3 backend.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/multi-modal-ui.service`:

```ini
[Unit]
Description=Multi-Modal Agent UI
After=network.target multi-modal-backend.service

[Service]
Type=simple
User=app
WorkingDirectory=/path/to/app
ExecStart=/usr/bin/streamlit run frontend/app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable multi-modal-backend
systemctl enable multi-modal-ui
systemctl start multi-modal-backend
systemctl start multi-modal-ui
```

---

### What to Do Next

1. **Test the UI** - Try all 4 task types
2. **Customize** - Modify agents, add features
3. **Deploy** - Use Docker or systemd
4. **Monitor** - Check logs and health
5. **Scale** - Add caching, rate limiting
6. **Integrate** - Connect to other systems

---

### Documentation

See these files for more info:

- **BACKEND_QUICKSTART.md** - Backend setup (3 steps)
- **BACKEND_API.md** - Complete API documentation
- **STREAMLIT_GUIDE.md** - Detailed UI guide
- **PROJECT_OVERVIEW.md** - Complete project overview

---

### Support Checklist

When something goes wrong:

- [ ] Check both terminal windows have no errors
- [ ] Verify HF_API_KEY is set correctly
- [ ] Run health check: `curl http://localhost:8000/health`
- [ ] Check API docs: http://localhost:8000/docs
- [ ] Review logs in terminal windows
- [ ] Try clearing history (🗑️ button)
- [ ] Restart UI (`Ctrl+C` and rerun)
- [ ] Restart backend (`Ctrl+C` and rerun)
- [ ] Check you have internet connection
- [ ] Verify HF API key is valid

---

### Quick Commands

```bash
# Start backend
python backend.py

# Start UI
streamlit run frontend/app.py

# Check API health
curl http://localhost:8000/health

# Run examples
python backend_example.py

# Install dependencies
pip install -r requirements.txt

# Set API key (Linux/macOS)
export HF_API_KEY="your-key"

# Set API key (Windows PowerShell)
$env:HF_API_KEY="your-key"

# View API docs
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
start http://localhost:8000/docs  # Windows

# View Streamlit UI
open http://localhost:8501  # macOS
xdg-open http://localhost:8501  # Linux
start http://localhost:8501  # Windows
```

---

### Success Indicators

✅ You're good if you see:

1. **Backend Terminal**:
   ```
   INFO: Uvicorn running on http://0.0.0.0:8000
   ```

2. **Streamlit Terminal**:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   ```

3. **Streamlit UI**:
   - ✓ API Connected (green checkmark)
   - Can type text and submit
   - Can upload images
   - Results display correctly

4. **API Health**:
   - http://localhost:8000/health returns status: "healthy"

---

### You're All Set! 🎉

Everything is working if you completed all tests above.

Now you can:
- Use the UI for processing
- Try different prompts
- Upload and analyze images
- Integrate with other systems
- Deploy to production

Enjoy your multi-modal agent!

---
"""

if __name__ == "__main__":
    print(__doc__)
