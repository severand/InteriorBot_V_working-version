# 🚀 DEPLOYMENT GUIDE - Qwen-VL Facade Analyzer

## 📋 Quick Checklist

- [ ] Clone/pull `feature/qwen-vl-facade-analyzer` branch
- [ ] Install dependencies
- [ ] Test locally
- [ ] Configure for your environment
- [ ] Deploy

---

## 🔧 LOCAL SETUP (5 minutes)

### 1. Get the code

```bash
# Clone repo if you haven't
git clone https://github.com/severand/InteriorBot_V_working-version.git
cd InteriorBot_V_working-version

# Switch to feature branch
git checkout feature/qwen-vl-facade-analyzer
```

### 2. Install dependencies

```bash
# Install Qwen-VL specific requirements
pip install -r bot/services/qwen_facade_analyzer/requirements.txt

# Or add to your main requirements.txt
cat bot/services/qwen_facade_analyzer/requirements.txt >> requirements.txt
pip install -r requirements.txt
```

### 3. Test the analyzer

```bash
# Get a test image (any house facade photo)
# Let's say you saved it as test_facade.jpg

cd bot/services/qwen_facade_analyzer
python test_analyzer.py /path/to/test_facade.jpg
```

**Expected output:**
```
======================================================================
🚀 QWEN-VL FACADE ANALYZER TEST
======================================================================

📸 Image: test_facade.jpg
✅ Image loaded: (1920, 1080)

📥 Loading Qwen-VL model...
✅ Model loaded successfully

🔄 Generating analysis...
✅ Analysis complete

📊 RESULT:
======================================================================
This is a modern two-story residential building with...
[DETAILED ANALYSIS]
======================================================================
```

---

## 🐳 DOCKER DEPLOYMENT

### Option A: Add to existing Docker image

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY bot/services/qwen_facade_analyzer/requirements.txt /tmp/qwen_requirements.txt
COPY requirements.txt /tmp/requirements.txt

# Install Python packages
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/qwen_requirements.txt

# Copy bot code
COPY bot /app/bot
WORKDIR /app

# Run bot
CMD ["python", "-m", "bot.main"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - KIE_API_KEY=${KIE_API_KEY}
      - GPU_ENABLED=true  # Set to false if no GPU
    volumes:
      - ./data:/app/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]  # Comment out if no GPU
```

### Build and run

```bash
# Build
docker build -t interiorbot:qwen-vl .

# Run
docker run --gpus all -v $(pwd)/data:/app/data interiorbot:qwen-vl
```

---

## ☁️ CLOUD DEPLOYMENT

### AWS EC2 (with GPU)

```bash
# Launch EC2 instance with GPU support (g4dn.xlarge or better)
# AMI: Deep Learning AMI (Amazon Linux 2)

# SSH into instance
ssh -i key.pem ec2-user@instance-ip

# Install PyTorch with CUDA
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# Clone and setup
git clone https://github.com/severand/InteriorBot_V_working-version.git
cd InteriorBot_V_working-version
git checkout feature/qwen-vl-facade-analyzer

pip install -r bot/services/qwen_facade_analyzer/requirements.txt

# Run bot
python -m bot.main
```

### Google Cloud Run (CPU)

```bash
# Note: For Qwen-VL, GPU recommended. CPU will be slow.

# Create Cloud Run service
gcloud run deploy interiorbot-facade \
  --source . \
  --platform managed \
  --memory 8G \
  --timeout 600 \
  --set-env-vars TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
```

### Hugging Face Spaces

```bash
# Create new Space
# Upload files:
# - bot/services/qwen_facade_analyzer/
# - requirements.txt
# - app.py (Gradio/Streamlit interface)

# In Space, enable GPU via Settings
```

---

## 🔌 INTEGRATION STEPS

### 1. Add to your bot's main.py

```python
from services.qwen_facade_analyzer import get_facade_analyzer
from services.qwen_facade_analyzer.integration_example import FacadeTransformationHandler

# Initialize
facade_handler = FacadeTransformationHandler(bot, kie_ai_client=your_kie_client)

# In message handler
@bot.message_handler(content_types=['photo'])
async def handle_photo(message):
    # Check if it's a facade photo
    file_path = await bot.download_file(message.photo[-1])
    await facade_handler.handle_facade_photo(message.chat.id, file_path)
```

### 2. Add to your services

```python
# services/__init__.py
from .qwen_facade_analyzer import get_facade_analyzer
```

### 3. Update main requirements.txt

```bash
# Add to requirements.txt
echo "" >> requirements.txt
cat bot/services/qwen_facade_analyzer/requirements.txt >> requirements.txt
```

---

## 📊 PERFORMANCE TUNING

### GPU Acceleration

```python
from services.qwen_facade_analyzer import get_facade_analyzer

# Use 7B model for best quality
analyzer = get_facade_analyzer(model_size="7b")

# Requires: 24GB+ VRAM for 7B
# or: 16GB+ VRAM for 7B with 8-bit quantization
```

### Quantization (8-bit, 4-bit)

```python
# Install bitsandbytes
pip install bitsandbytes

# In analyzer.py, modify _load_model():
self.model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype="auto",
    load_in_8bit=True,  # 8-bit quantization
    device_map="auto"
)
```

### Smaller Model for Limited Resources

```python
# Use 2B model
analyzer = get_facade_analyzer(model_size="2b")
# Requires: 4-8GB VRAM
```

---

## 📈 MONITORING

### Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Analyzer initialized")
logger.info("Analysis complete: 500 chars")
```

### Metrics to track

- Analysis time (should be 20-60 seconds)
- GPU memory usage
- API success rate
- User satisfaction (collect feedback)

---

## 🐛 TROUBLESHOOTING

### Model Download Error

```bash
# Pre-download model
hf_hub_download(
    repo_id="Qwen/Qwen2-VL-7B-Instruct",
    cache_dir="./models"
)
```

### Out of Memory

```python
# Switch to 2B
analyzer = get_facade_analyzer(model_size="2b")

# Or use 8-bit quantization
```

### Slow Inference on CPU

```bash
# Install ONNX Runtime for CPU optimization
pip install onnxruntime
```

---

## 📝 PRODUCTION CHECKLIST

- [ ] Tested locally with GPU
- [ ] Set appropriate model size (7b or 2b)
- [ ] Configured logging
- [ ] Set up monitoring
- [ ] Prepared error handling
- [ ] Documented deployment steps
- [ ] Set rate limiting
- [ ] Configured caching (optional)
- [ ] Set up backup inference (fallback)
- [ ] Tested end-to-end flow

---

## 🚀 READY TO DEPLOY!

Your Qwen-VL Facade Analyzer is ready for production. Next steps:

1. **Test locally** - `python test_analyzer.py test_facade.jpg`
2. **Deploy to your environment** - Follow Docker/Cloud section
3. **Integrate with your bot** - Copy handler code
4. **Monitor performance** - Track metrics
5. **Iterate** - Improve prompts based on results

---

## 📞 SUPPORT

- GitHub Issues: [Create issue](https://github.com/severand/InteriorBot_V_working-version/issues)
- Documentation: See README.md
- Examples: See integration_example.py

---

**Branch:** `feature/qwen-vl-facade-analyzer`  
**Status:** ✅ Production Ready  
**Last Updated:** 2026-01-05
