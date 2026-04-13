"""
Streamlit Frontend - Usage Guide

Complete guide to running the ChatGPT-like Streamlit UI for the multi-modal agent.
"""

# ============================================================================
# STREAMLIT UI - COMPLETE GUIDE
# ============================================================================

"""
## Multi-Modal Agent - Streamlit Frontend

A modern, ChatGPT-like web interface for the multi-modal AI agent.

### Features

✅ **Conversation History** - Persistent chat log with timestamps
✅ **Text Input** - Large text area for prompts with placeholder text
✅ **Image Upload** - Support for JPG, PNG, GIF images
✅ **Task Auto-Detection** - Automatically routes to correct agent
✅ **Real-time Results** - Displays results as they arrive
✅ **Download Support** - Download generated images
✅ **Verbose Mode** - Optional detailed execution trace
✅ **API Status** - Shows connection health
✅ **Settings** - Configure API URL and timeout
✅ **Clean Design** - Modern UI with colors and animations

---

### Quick Start

#### 1. Make sure backend is running
```bash
python backend.py
```

#### 2. Run Streamlit UI
```bash
streamlit run frontend/app.py
```

#### 3. Open in browser
- Automatically opens at http://localhost:8501
- Or manually visit: http://localhost:8501

### Browser Support

- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers (responsive design)

---

### UI Components

#### 1. Header & Status

- **Title**: "🤖 Multi-Modal Agent"
- **Subtitle**: "Your AI assistant for text and image processing"
- **API Status**: Shows ✓ or ✗ connection status
- **Buttons**:
  - 🔄 Check Health - Refresh API connection status
  - ⚙️ Settings - Open advanced settings

#### 2. Main Content Area (2-column layout)

**Left Column (Chat Area - 75% width)**:
- Chat history with messages
- User messages (blue background)
- Assistant messages (gray background)
- Timestamps for each message
- Task type badges (colored labels)
- Displayed images in chat

**Right Column (Sidebar - 25% width)**:
- About section with capabilities
- Tips for each task type
- Clear History button
- Settings (when expanded)

#### 3. Input Section

**Text Area**:
- Placeholder: "Type something or paste text..."
- Height: 100px
- Max length: 10,000 characters
- Auto-resize on overflow

**Options**:
- Image upload (drag & drop or click)
- Verbose checkbox (detailed trace)

**Submit Button**:
- Green button (#10a37f)
- Full width
- Loading spinner while processing

#### 4. Results Display

**Summarization Results**:
- ✓ Success indicator
- Displayed summary text
- Execution trace (collapsible)

**Sentiment/Stance Analysis**:
- Metric cards: Sentiment, Confidence, Status
- Progress bars for all scores
- Detailed breakdown

**Image Generation**:
- Generated image preview
- Download button with timestamp
- Execution trace

**Image Analysis**:
- Top 5 predictions
- Progress bars for confidence scores
- Numbered ranking

#### 5. Settings Panel

- **API URL**: Change backend address (default: http://localhost:8000)
- **Timeout**: Set request timeout in seconds (10-300)
- **Test Connection**: Verify API availability

---

### Supported Tasks

#### Task 1: Text Summarization

**How to trigger**:
- Type: "Summarize this article..."
- Type: "Can you give me a summary?"
- Type: "Condense this text"

**Output**:
- Summary text
- Execution trace showing chunking if needed

**Example**:
```
User: Summarize this long article about AI...
→ Task detected: SUMMARIZATION
→ Agent: facebook/bart-large-cnn
→ Output: A short summary of the article
```

#### Task 2: Sentiment/Stance Analysis

**How to trigger**:
- Type: "What's the sentiment?"
- Type: "Analyze my opinion"
- Type: "Detect sentiment in this"

**Output**:
- Sentiment label: positive, negative, neutral
- Confidence percentage
- All scores breakdown

**Example**:
```
User: I absolutely love this product!
→ Task detected: STANCE_DETECTION
→ Agent: facebook/bart-large-mnli (zero-shot)
→ Output: positive (99.5% confidence)
```

#### Task 3: Image Generation

**How to trigger**:
- Type: "Generate a sunset"
- Type: "Draw a mountain landscape"
- Type: "Create an image of..."

**Output**:
- Generated image display
- Image size info
- Download button

**Example**:
```
User: Generate a serene mountain landscape at sunset
→ Task detected: IMAGE_GENERATION
→ Agent: stabilityai/stable-diffusion-2
→ Output: 512x512 PNG image
```

#### Task 4: Image Analysis

**How to trigger**:
- Upload an image (with any text)
- Type: "Analyze this image"
- Type: "What's in this photo?"

**Output**:
- Top 5 predictions with scores
- Confidence percentages
- ImageNet class labels

**Example**:
```
User: [uploads dog.jpg] Analyze this image
→ Task detected: IMAGE_ANALYSIS
→ Agent: google/vit-base-patch16-224
→ Output: 
  1. dog: 95.2%
  2. puppy: 3.1%
  3. canine: 1.2%
  ...
```

---

### Session Management

#### Conversation History

- Stored in `st.session_state.messages`
- Persists during session
- Cleared when:
  - Browser refreshed (loses state)
  - Click "🗑️ Clear History" button
  - Restart Streamlit app

**Message Structure**:
```python
{
    "role": "user" | "assistant",
    "content": "message text",
    "timestamp": "HH:MM:SS",
    "task_type": "summary" | "stance" | "image_gen" | "image_analysis",
    "success": True | False,
    "image": base64_encoded_bytes  # only for user messages with images
}
```

#### Session State Tracking

- `messages`: Conversation history list
- `api_available`: API connection status boolean
- `uploaded_image`: Current file uploader state
- `show_settings`: Settings panel visibility

---

### Error Handling

#### API Connection Errors

**Error**: "✗ API Disconnected"
**Solution**:
1. Make sure backend is running: `python backend.py`
2. Check backend is on http://localhost:8000
3. Click "🔄 Check Health" to refresh status

**Error**: "Cannot connect to API"
**Solution**:
- Verify backend is running
- Check backend logs for errors
- Try different API URL in settings
- Restart both backend and frontend

#### Input Validation Errors

**Error**: "❌ Please enter some text"
**Solution**:
- Type something in the text area
- Can't submit empty messages

**Error**: "Image too large (max 50MB)"
**Solution**:
- Use smaller image file
- Compress image before upload
- Try JPG format (smaller than PNG)

#### Processing Errors

**Error**: "Request timeout"
**Solution**:
- Increase timeout in settings (60+ seconds)
- Try again (models might be loading)
- Check server logs

**Error**: "Processing failed"
**Solution**:
- Check execution trace for details
- Enable verbose mode for more info
- Check backend logs
- Restart backend

---

### Keyboard Shortcuts

- **Ctrl+Enter** (in text area most systems): Quick submit
- **Tab**: Navigate between elements
- **Click "Chat History"**: Focus on messages
- **Scroll**: Navigate chat, upload areas

---

### Tips & Tricks

#### 1. Copy Results

- Text results: Triple-click to select all
- Images: Right-click → Save image as...
- Or use download button for images

#### 2. Batch Processing

Multiple queries at once:
```
1. "Summarize article1" → Submit
2. "Summarize article2" → Submit
3. "Summarize article3" → Submit

Results show in chronological order
```

#### 3. Verbose Mode

Enable "Verbose" checkbox to see:
- Agent initialization
- Model loading status
- Processing steps
- Each stage of workflow

#### 4. API Debug Info

With verbose enabled, execution trace shows:
- Router decisions
- Agent selection
- Processing time
- Model names used

#### 5. Image Upload Best Practices

- **Format**: JPG or PNG recommended
- **Size**: Under 10MB ideal
- **Resolution**: Any size works
- **Drag & Drop**: Supported
- **Multiple**: Upload one at a time

#### 6. Custom API Server

If backend on different machine:
1. Click ⚙️ Settings
2. Change "API URL" to: http://other-machine:8000
3. Click "Test Connection"
4. Should show ✓ Connected to API

---

### Performance Optimization

#### 1. First Load (Slow)

- Models load on first use
- Can take 30-120 seconds
- Subsequent requests faster
- This is normal

**Timeline**:
- Load UI: 2-3 seconds
- First API call: 30-120 seconds (model loading)
- Subsequent calls: 3-15 seconds

#### 2. Session Optimization

- Clear history if getting slow
- Restart Streamlit if hanging
- Check system RAM (models need memory)
- Close other heavy applications

#### 3. Network Optimization

- Use same machine (localhost)
- For remote: use VPN/direct connection
- Check network latency

---

### Advanced Usage

#### Custom Prompts

**For Summarization**:
- "Summarize in 50 words"
- "Key points from this text"
- "Abstract of this article"

**For Sentiment**:
- "Detect my opinion"
- "Is this positive or negative?"
- "Analyze this review"

**For Image Generation**:
- "Generate a sunset, oil painting style"
- "Create a sci-fi landscape"
- "Digital art of a space city"

**For Image Analysis**:
- "What objects are in this?"
- "Identify what you see"
- "Classify this image"

#### Multi-turn Conversations

While not true multi-turn yet, you can:
1. Generate image → Download
2. Upload downloaded image → Analyze
3. Get results → Use in next prompt

#### Batch Operations

Use `/process-batch` endpoint directly:
```python
import requests

texts = ["Text 1", "Text 2", ...]
response = requests.post(
    "http://localhost:8000/process-batch",
    data={"texts": texts}
)
```

---

### Deployment

#### Local Development
```bash
streamlit run frontend/app.py
```

#### Production (Recommended)
```bash
streamlit run frontend/app.py \\
  --logger.level=warning \\
  --client.showErrorDetails=false
```

#### With HTTPS (Self-signed cert)
```bash
# Requires proxy like nginx
# Configure nginx to reverse proxy to :8501
```

#### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501"]
```

```bash
docker build -t multi-modal-ui .
docker run -p 8501:8501 multi-modal-ui
```

---

### Troubleshooting

#### Issue: "ModuleNotFoundError: No module named 'streamlit'"

**Solution**:
```bash
pip install streamlit
# or
pip install -r requirements.txt
```

#### Issue: "Connection refused" or "Cannot connect to API"

**Solution**:
1. Check backend is running: `python backend.py`
2. Check it's on correct port: http://localhost:8000
3. In Streamlit settings, verify API URL
4. Try: `curl http://localhost:8000/health`

#### Issue: "Session state reset on page load"

**Expected behavior**: 
- State resets on browser refresh (normal Streamlit behavior)
- Use `st.cache_data` if you need persistence

#### Issue: "Image not displaying"

**Solution**:
- Try different image format (JPG instead of PNG)
- Reduce image size
- Check browser console for errors (F12)

#### Issue: "Slow responses"

**Solution**:
1. Increase timeout in settings
2. First request loads models (slow)
3. Check if backend is running smoothly
4. Monitor CPU/RAM usage
5. Try with smaller input

#### Issue: "Timeout errors"

**Solution**:
1. Increase API timeout (settings)
2. Verify network connection
3. Check server isn't overloaded
4. Restart backend
5. Try from same machine (localhost)

---

### Settings Reference

#### API Configuration

| Setting | Default | Range | Purpose |
|---------|---------|-------|---------|
| API URL | http://localhost:8000 | Any URL | Backend server address |
| Timeout | 60 seconds | 10-300 | Request timeout |

#### File Size Limits

| Limit | Size | Reason |
|-------|------|--------|
| Max Image | 50MB | Memory/bandwidth |
| Max Text | 10,000 chars | API limit |
| Max Batch | 100 items | Processing |

---

### Browser Storage

Streamlit stores in browser:
- Session state (until refresh)
- Chat history (cleared on refresh)
- Settings (UI state)

To clear everything:
1. Click "🗑️ Clear History"
2. Refresh browser (Ctrl+R)
3. Or open in incognito/private mode

---

### Keyboard & Accessibility

- ✅ Tab navigation supported
- ✅ Screen reader compatible
- ✅ Keyboard input accepted
- ✅ Color contrast adequate
- ✅ Mobile responsive

---

### Support & Debugging

#### Enable Debug Logs

```bash
streamlit run frontend/app.py --logger.level=debug
```

#### Check Requests

If stuck, check backend logs:
```bash
# In backend/app.py running terminal
# Watch for INFO/ERROR logs
```

#### API Test (without Streamlit)

```bash
curl -X POST http://localhost:8000/process \\
  -F "text=Test input"
```

---

### Next Steps

1. ✅ Start backend: `python backend.py`
2. ✅ Start frontend: `streamlit run frontend/app.py`
3. ✅ Try all 4 task types
4. ✅ Test with images
5. ✅ Enable verbose mode
6. ✅ Check execution trace
7. ✅ Deploy (Docker/systemd)
8. ✅ Integrate with other systems

---

### Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **Backend API**: http://localhost:8000/docs (Swagger)
- **Rerun Behavior**: https://docs.streamlit.io/concepts/app-model
- **Session State**: https://docs.streamlit.io/concepts/session-state

---
"""

if __name__ == "__main__":
    print(__doc__)
