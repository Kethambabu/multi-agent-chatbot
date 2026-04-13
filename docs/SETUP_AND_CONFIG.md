# Environment Setup & Configuration Guide

## Quick Start

### 1. Get Your Hugging Face API Key

1. Go to https://huggingface.co/settings/tokens
2. Click "Create new token"
3. Give it a name (e.g., "multi-modal-agent")
4. Select read-only access
5. Copy the token

### 2. Create `.env` File

Copy `.env.example` to `.env` and add your API key:

```bash
# Copy template
cp .env.example .env

# Edit .env with your editor
# Add your API key:
HF_API_KEY=hf_your_actual_token_here
```

**IMPORTANT:** 
- `.env` is in `.gitignore` - it will NEVER be committed
- Never share your API key
- Never paste it in code comments

Example `.env`:
```env
HF_API_KEY=hf_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
HF_TIMEOUT=30
HF_MAX_RETRIES=3
DEBUG=false
API_PORT=8000
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** No local models are downloaded. The system uses **Hugging Face Inference API only**.

### 4. Run the Application

**Start Backend:**
```bash
python backend.py
```

**Start Frontend (new terminal):**
```bash
streamlit run frontend/app.py
```

Visit: http://localhost:8501

---

## Configuration Reference

All configuration uses environment variables. No hardcoded values.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `HF_API_KEY` | Hugging Face API token | `hf_xxxxxxxxxxxx` |

Get from: https://huggingface.co/settings/tokens

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TIMEOUT` | 30 | API request timeout (seconds) |
| `HF_MAX_RETRIES` | 3 | Max retry attempts for failed requests |
| `HF_MODEL_LOADING_TIMEOUT` | 120 | Timeout for model loading (seconds) |
| `API_HOST` | 0.0.0.0 | FastAPI server host |
| `API_PORT` | 8000 | FastAPI server port |
| `API_RELOAD` | false | Auto-reload on code changes (dev only) |
| `API_WORKERS` | 4 | Number of worker processes |
| `DEBUG` | false | Enable debug logging |
| `MODEL_NAME` | multi-modal-agent | Application name |
| `MAX_IMAGE_SIZE` | 52428800 | Max image upload size (bytes) |
| `MAX_BATCH_SIZE` | 100 | Max items per batch request |

---

## Environment Variables in Different Shells

### Linux / macOS (Bash/Zsh)

```bash
# Temporary (current session only)
export HF_API_KEY="hf_your_token"

# Verify it's set
echo $HF_API_KEY

# Permanent - add to ~/.bashrc or ~/.zshrc
echo 'export HF_API_KEY="hf_your_token"' >> ~/.bashrc
source ~/.bashrc
```

### Windows (PowerShell)

```powershell
# Temporary (current session only)
$env:HF_API_KEY="hf_your_token"

# Verify it's set
echo $env:HF_API_KEY

# Permanent (PowerShell profile)
Add-Content $PROFILE '$env:HF_API_KEY="hf_your_token"'
. $PROFILE
```

### Windows (CMD)

```cmd
# Temporary (current session only)
set HF_API_KEY=hf_your_token

# Verify it's set
echo %HF_API_KEY%

# Permanent (System Environment Variables)
setx HF_API_KEY "hf_your_token"
```

### Using .env File (Recommended)

Create `.env` in project root. Python automatically loads it:

```env
HF_API_KEY=hf_your_token_here
HF_TIMEOUT=30
DEBUG=false
API_PORT=8000
```

The `python-dotenv` library automatically loads `.env` on startup.

---

## Using Configuration in Code

### Load Configuration

```python
from config import get_config

# Get global config instance
config = get_config()

# Access settings
print(config.hf_api_key)      # Never print in production!
print(config.api_port)         # 8000
print(config.debug)            # false
```

### Print Configuration (Safe)

```python
from config import print_config_info

# Prints all settings except API key
print_config_info()
```

### Create HF Client

```python
from utils.hf_client import HFClient, HFClientConfig
from config import get_config

config = get_config()

# Create client (uses config automatically)
hf_config = HFClientConfig(
    api_key=config.hf_api_key,
    timeout=config.timeout,
    max_retries=config.max_retries
)

client = HFClient(hf_config)
```

---

## Models Used (API-Based)

The system uses these Hugging Face models via **Inference API only**:

| Task | Model | API Endpoint |
|------|-------|-------------|
| Summarization | facebook/bart-large-cnn | `api-inference.huggingface.co/models/facebook/bart-large-cnn` |
| Stance Detection | facebook/bart-large-mnli | `api-inference.huggingface.co/models/facebook/bart-large-mnli` |
| Image Generation | stabilityai/stable-diffusion-2 | `api-inference.huggingface.co/models/stabilityai/stable-diffusion-2` |
| Image Analysis | google/vit-base-patch16-224 | `api-inference.huggingface.co/models/google/vit-base-patch16-224` |

**No models are downloaded locally.** All inference happens via HTTPS API calls.

---

## API Architecture

### How Requests Flow

```
User Input
    ↓
[Backend API] (/process endpoint)
    ↓
[Config] (loads HF_API_KEY)
    ↓
[HFClient] (manager/hf_client.py)
    ↓
[HTTPS Request] → api-inference.huggingface.co
    ↓
[Hugging Face Servers] (inference on their hardware)
    ↓
[Response] (JSON or bytes)
    ↓
[Agent] processes response
    ↓
[Result] returned to user
```

### Example: Text Summarization

```python
# 1. Load config (automatically from .env or environment)
config = get_config()

# 2. Create HF client
client = HFClient(HFClientConfig(api_key=config.hf_api_key))

# 3. Call Hugging Face Inference API
response = client.request(
    model="facebook/bart-large-cnn",
    payload={"inputs": "Long text to summarize..."},
    task="summarization"
)

# 4. Get result
summary = response[0]["summary_text"]
```

No local models, no downloads, no GPU requirements.

---

## Troubleshooting

### Error: "HF_API_KEY environment variable is not set"

**Solution:**
1. Create `.env` file with your API key
2. Or set it in your system environment
3. Never hardcode it in Python files

```bash
# Quick test
python -c "from config import get_config; config = get_config(); print('✓ Config loaded')"
```

### Error: "Authentication failed"

**Cause:** Invalid or expired API key

**Solution:**
1. Get a new token from https://huggingface.co/settings/tokens
2. Update `.env` file
3. Restart the application

### Error: "Model is loading" / HTTP 503

**Cause:** Model is being loaded on Hugging Face servers (happens on first request)

**Solution:**
- Normal on first request (~30-60 seconds)
- System auto-retries
- Subsequent requests are fast (model cached)

### Error: "Request timed out"

**Solution:**
Increase timeout in `.env`:
```env
HF_TIMEOUT=60
HF_MODEL_LOADING_TIMEOUT=180
```

### High API Usage / Costs

**Note:** The free tier of Hugging Face Inference API has rate limits. For production:

1. Upgrade to Hugging Face Pro (paid tier)
2. Or use Hugging Face Inference Endpoints (dedicated)
3. Monitor your usage at https://huggingface.co/settings/billing/overview

---

## Security Best Practices

### ✅ DO:

- ✅ Store API key in `.env` file
- ✅ Add `.env` to `.gitignore`
- ✅ Use environment variables
- ✅ Never commit API keys
- ✅ Rotate keys regularly
- ✅ Use `.env.example` as template
- ✅ Validate config on startup
- ✅ Log without sensitive data

### ❌ DON'T:

- ❌ Hardcode API keys in Python files
- ❌ Paste API keys in comments
- ❌ Commit `.env` to version control
- ❌ Share API key in error messages
- ❌ Print config with API key
- ❌ Use same key across environments
- ❌ Store keys in databases
- ❌ Email or chat API keys

---

## Development vs Production

### Development (.env file)

```env
HF_API_KEY=hf_your_dev_token
DEBUG=true
API_RELOAD=true
HF_TIMEOUT=60
```

```bash
# Run with auto-reload
python backend.py
```

### Production (Environment Variables)

```bash
# Set via shell/container/CI-CD
export HF_API_KEY="hf_prod_token_hash_or_secret"
export DEBUG=false
export API_WORKERS=8
export HF_TIMEOUT=30

# Run
python backend.py
```

---

## Architecture: API-Only Design

### What Changed

| Old Architecture | New Architecture |
|---|---|
| Download models locally | Stream from Hugging Face API |
| Use transformers pipeline | Call HTTPS endpoints |
| Store in ~/.cache/ | No local cache |
| Slow first startup | Instant startup |
| High disk/memory | Minimal resources |
| Hardcoded keys | Environment variables |

### Benefits

✅ **No Model Downloads** - Models stay on Hugging Face servers
✅ **Always Latest** - Automatic model updates
✅ **Minimal Disk** - No 10GB+ model storage
✅ **Secure** - Keys in environment, not code
✅ **Scalable** - Use multiple API keys for load balancing
✅ **Stateless** - Easy to containerize/deploy
✅ **Cost Efficient** - Pay only for what you use

### Trade-offs

- Requires internet connection
- API rate limits / costs
- API availability depends on Hugging Face
- ~1-3 second latency per request (vs <100ms locally)

---

## Configuration Validation

The system validates configuration on startup:

```python
from config import get_config

try:
    config = get_config()
    # Config is validated and ready to use
    print(f"✓ Running on {config.api_host}:{config.api_port}")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
    exit(1)
```

Validation checks:
- ✅ HF_API_KEY is set
- ✅ All timeouts are positive
- ✅ Port is valid (1-65535)
- ✅ File size limits are positive
- ✅ Worker count is positive

---

## Examples

### Example: Check Configuration

```python
from config import get_config, print_config_info

config = get_config()
print_config_info()
# Outputs all settings (API key excluded for security)
```

### Example: Create Custom Config

```python
from config import Config
import os

os.environ["HF_API_KEY"] = "hf_your_token"
os.environ["HF_TIMEOUT"] = "60"
os.environ["DEBUG"] = "true"

config = Config()
config.validate()

print(f"Timeout: {config.timeout}s")
print(f"Debug: {config.debug}")
```

### Example: Use Config in Agent

```python
from config import get_config
from agents.summarizer import SummarizerAgent
from utils.hf_client import HFClientConfig

config = get_config()

hf_config = HFClientConfig(
    api_key=config.hf_api_key,
    timeout=config.timeout,
    max_retries=config.max_retries
)

agent = SummarizerAgent(hf_config)
summary = agent.summarize("Long text here...")
```

---

## Next Steps

1. ✅ Create `.env` file with your HF_API_KEY
2. ✅ Install dependencies: `pip install -r requirements.txt`
3. ✅ Run tests: `python -m pytest` (if tests exist)
4. ✅ Start backend: `python backend.py`
5. ✅ Start frontend: `streamlit run frontend/app.py`
6. ✅ Visit: http://localhost:8501

---

## Further Reading

- **Hugging Face API Docs**: https://huggingface.co/docs/api-inference
- **Hugging Face Hub**: https://huggingface.co
- **Python dotenv**: https://python-dotenv.readthedocs.io
- **FastAPI Config**: https://fastapi.tiangolo.com/advanced/settings/

