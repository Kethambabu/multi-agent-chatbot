# 🚀 How to Run Multi-Modal AI Agent Project

## Prerequisites

- Python 3.9 or higher
- Git (optional)
- HuggingFace API Token (required)
- Internet connection (for API calls)

---

## Step 1: Setup Environment Variable

### Get Your HuggingFace API Token

1. Go to: [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token (if you don't have one)
3. Copy the token

### Create `.env` File

**Windows (PowerShell):**
```powershell
cd c:\Users\N Balu\Downloads\multi_modal_agent
Copy-Item .env.example .env
# Open .env in your editor and add your HF_API_KEY
```

**Windows (CMD):**
```cmd
cd c:\Users\N Balu\Downloads\multi_modal_agent
copy .env.example .env
:: Edit .env file and add your HF_API_KEY
```

**Edit `.env` file:**
```env
HF_API_KEY=hf_YOUR_API_TOKEN_HERE
# Replace YOUR_API_TOKEN_HERE with your actual token

# Other optional settings (defaults are fine):
HF_TIMEOUT=30
HF_MAX_RETRIES=3
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=8501
DEBUG=false
```

---

## Step 2: Activate Virtual Environment

The virtual environment (`venv`) has already been created. Activate it:

### Windows (PowerShell):
```powershell
cd c:\Users\N Balu\Downloads\multi_modal_agent
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows (CMD):
```cmd
cd c:\Users\N Balu\Downloads\multi_modal_agent
venv\Scripts\activate.bat
```

### macOS/Linux:
```bash
cd ~/Downloads/multi_modal_agent
source venv/bin/activate
```

---

## Step 3: Install Dependencies

All dependencies are listed in `requirements.txt` and will be installed automatically.

**Note:** This might take 2-5 minutes on first install.

```powershell
pip install -r requirements.txt
```

Verify installation:
```powershell
python -c "from config import get_config; c = get_config(); print('✓ Configuration loaded successfully!')"
```

---

## Step 4: Run the Project

### Option A: Run Backend Only

The backend API server runs on `http://0.0.0.0:8000`

```powershell
python app.py
```

Expected output:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

API Documentation: `http://localhost:8000/docs`

---

### Option B: Run Frontend Only

The frontend UI runs on `http://localhost:8501` (Streamlit)

**In a new terminal (with venv activated):**

```powershell
streamlit run frontend/app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  URL: http://localhost:8501
```

---

### Option C: Run Both (Recommended)

Run backend and frontend together:

**Terminal 1 - Backend:**
```powershell
cd c:\Users\N Balu\Downloads\multi_modal_agent
.\venv\Scripts\Activate.ps1
python app.py
```

**Terminal 2 - Frontend:**
```powershell
cd c:\Users\N Balu\Downloads\multi_modal_agent
.\venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

---

## Project Structure

```
c:\Users\N Balu\Downloads\multi_modal_agent\
├── venv\                      ← Virtual environment (created)
├── .env                       ← Your API keys (NEVER commit!)
├── .env.example              ← Template (safe to commit)
├── .gitignore               ← Excludes .env from git
├── config.py                ← Configuration management
├── app.py                   ← Backend API (FastAPI)
├── requirements.txt          ← Python dependencies
│
├── docs\                    ← Documentation folder
│   ├── HOW_TO_RUN.md       ← This file
│   ├── SETUP_AND_CONFIG.md ← Setup guide
│   ├── BEFORE_AND_AFTER.md ← Refactoring changes
│   └── ... (other docs)
│
├── agents\                  ← AI agents for different tasks
│   ├── summarizer.py       ← Text summarization
│   ├── stance.py           ← Sentiment analysis
│   ├── text2image.py       ← Image generation
│   └── image_analysis.py   ← Image classification
│
├── graph\                   ← Workflow orchestration
│   ├── state.py            ← State management
│   └── workflow.py         ← Task orchestration
│
├── frontend\                ← Streamlit frontend
│   └── app.py              ← Web interface
│
└── utils\                   ← Utility modules
    ├── hf_client.py        ← HuggingFace API client
    └── HF_CLIENT_DOCS.md   ← Client documentation
```

---

## API Endpoints (Backend)

Once backend is running, access these endpoints:

### Interactive API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Example Endpoints
- **Summarization**: `POST /summarize`
- **Stance Detection**: `POST /detect_stance`
- **Text to Image**: `POST /generate_image`
- **Image Analysis**: `POST /analyze_image`

See `docs/BACKEND_API.md` for complete API documentation.

---

## Troubleshooting

### Issue: "HF_API_KEY not set"

**Solution:**
1. Make sure `.env` file exists in the project root
2. Add your API key to `.env`:
   ```env
   HF_API_KEY=hf_your_token_here
   ```
3. Restart the application

### Issue: "ModuleNotFoundError: No module named 'xxx'"

**Solution:**
1. Check that virtual environment is activated:
   ```powershell
   # You should see (venv) at the start of your prompt
   ```
2. Reinstall dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### Issue: "Streamlit port already in use (8501)"

**Solution:**
Change the port in `.env`:
```env
FRONTEND_PORT=8502
```

Then run:
```powershell
streamlit run frontend/app.py --server.port 8502
```

### Issue: "HuggingFace API timeout"

**Solution:**
Increase timeout in `.env`:
```env
HF_TIMEOUT=60
```

### Issue: Models downloading/loading slowly

**Solution:**
Your app uses **API-only**, no local downloads. If it's slow:
1. Check internet connection
2. Increase `HF_TIMEOUT` in `.env`
3. Check HuggingFace API status: https://status.huggingface.co

---

## Getting Help

### Documentation Files

- **Setup**: See `docs/SETUP_AND_CONFIG.md`
- **API Details**: See `docs/BACKEND_API.md`
- **Refactoring Changes**: See `docs/BEFORE_AND_AFTER.md`
- **Streamlit Guide**: See `docs/STREAMLIT_GUIDE.md`
- **LLM Routing**: See `docs/LLM_ROUTING.md`

### Common Commands

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Test configuration
python -c "from config import get_config; print(get_config().to_dict())"

# List installed packages
pip list

# Update requirements
pip freeze > requirements.txt

# Deactivate venv
deactivate
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_API_KEY` | (required) | HuggingFace API token |
| `HF_TIMEOUT` | 30 | Request timeout in seconds |
| `HF_MAX_RETRIES` | 3 | Retry attempts for failed requests |
| `API_HOST` | 0.0.0.0 | Backend API host |
| `API_PORT` | 8000 | Backend API port |
| `FRONTEND_PORT` | 8501 | Frontend (Streamlit) port |
| `DEBUG` | false | Enable debug logging |

---

## Next Steps

1. ✅ Create `.env` with API key
2. ✅ Activate virtual environment
3. ✅ Install dependencies
4. ✅ Run backend: `python app.py`
5. ✅ Run frontend: `streamlit run frontend/app.py`
6. ✅ Open browser: `http://localhost:8501`

---

## Quick Reference

### Start Fresh (Complete Setup)

```powershell
# 1. Navigate to project
cd c:\Users\N Balu\Downloads\multi_modal_agent

# 2. Activate environment
.\venv\Scripts\Activate.ps1

# 3. Install dependencies (if needed)
pip install -r requirements.txt

# 4. Run backend (Terminal 1)
python app.py

# 5. Run frontend (Terminal 2)
streamlit run frontend/app.py

# 6. Open browser to http://localhost:8501
```

---

**Last Updated:** April 11, 2026  
**Python Version:** 3.9+  
**Virtual Environment:** venv (created)  
**Dependencies:** All in requirements.txt

