# AI Embeddings Fix Guide

## Issue: JAX/PyTorch Compatibility

The AI recommendations feature requires Sentence-BERT, which has a dependency conflict between JAX and PyTorch.

**Error:**
```
module 'torch.utils._pytree' has no attribute 'register_pytree_node'
```

---

## Solution Options

### Option 1: Fresh Virtual Environment (Recommended)

Create a clean environment with compatible versions:

```bash
# Navigate to API directory
cd services/api

# Create new virtual environment
python -m venv venv_ai

# Activate it
# Windows:
venv_ai\Scripts\activate
# Linux/Mac:
source venv_ai/bin/activate

# Install compatible versions
pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers==2.2.2
pip install faiss-cpu==1.7.4

# Install other requirements
pip install -r requirements.txt

# Generate embeddings
python generate_embeddings.py
```

### Option 2: Fix Current Environment

Reinstall PyTorch with compatible version:

```bash
cd services/api

# Uninstall conflicting packages
pip uninstall torch torchvision jax jaxlib -y

# Reinstall with specific versions
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers==2.2.2
pip install faiss-cpu==1.7.4

# Generate embeddings
python generate_embeddings.py
```

### Option 3: Use Docker (Production-Ready)

The cleanest solution for production:

```bash
# Start all services including MinIO
docker-compose up -d

# Run embeddings generation inside container
docker-compose exec api python generate_embeddings.py
```

---

## After Fix: Generate Embeddings

Once dependencies are fixed, run:

```bash
cd services/api
python generate_embeddings.py
```

Expected output:
```
🤖 AI Embeddings Generation
====================================
📥 Loading Sentence-BERT model...
✅ Model loaded successfully!

📋 Processing Jobs
====================================
Found 10 jobs without embeddings

  ✓ Job 1/10: Software Engineer
  ✓ Job 2/10: Data Scientist
  ...
📊 Jobs: 10 successful, 0 failed

📄 Processing Resumes
====================================
Found 1 resumes without embeddings

  ✓ Resume 1/1: resume.txt
📊 Resumes: 1 successful, 0 failed

✅ Embeddings Generation Complete!
Total Embeddings Generated: 11
💡 AI recommendations are now enabled!
```

---

## Test Recommendations

After generating embeddings, test the API:

```bash
# Get job recommendations for a resume
curl http://localhost:8000/api/recommendations/jobs-for-resume/{resume_id}

# Get resume quality score
curl http://localhost:8000/api/recommendations/resume-quality/{resume_id}
```

---

## Alternative: Mock Embeddings (For Testing Only)

If you just want to test the UI without AI:

1. The system will return empty recommendations
2. Resume quality will show basic metrics (text length, skill count)
3. No vector similarity matching

This is NOT recommended for production but allows frontend testing.

---

## Technical Details

### What Embeddings Do:
- Convert text (jobs/resumes) into 384-dimensional vectors
- Enable semantic similarity search using FAISS
- Power AI job recommendations
- Calculate resume quality scores

### Models Used:
- **Sentence-BERT:** `all-MiniLM-L6-v2` (384 dimensions)
- **FAISS:** Flat L2 index for vector search
- **Skill Extraction:** spaCy NER + custom patterns

### Performance:
- Model size: ~90MB
- Embedding generation: ~100ms per document
- Search: <10ms for 10k vectors

---

## Troubleshooting

### "Model not found"
```bash
# Download model manually
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### "FAISS not installed"
```bash
pip install faiss-cpu==1.7.4
```

### "Out of memory"
- Reduce batch size in embeddings_service.py
- Process jobs/resumes in smaller batches
- Use CPU-only PyTorch (already configured)

---

## Status

- ✅ Embeddings service code: Ready
- ✅ Generation script: Created
- ❌ Dependencies: Conflict (needs fix)
- ❌ Embeddings: Not generated yet

**Next Step:** Choose a solution option above and run the fix!
