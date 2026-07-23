# Backend image for Hugging Face Spaces (Docker SDK).
#
# HF specifics baked in:
#   - listens on port 7860 (HF's expected app port)
#   - runs as uid 1000 (HF Spaces' non-root user) with writable cache dirs
#   - CPU-only torch (the default Linux wheel is CUDA and multi-GB — pinning the
#     CPU index keeps the build small and inside the build timeout)
#   - the MiniLM embedder is pre-downloaded into the image, so the first request
#     after a cold start does not pay the download
#
# Exact pins for the load-bearing / heavy stack: HF rebuilds the image remotely,
# so `>=`/`~=` could silently drift to an untested patch. These versions are the
# exact set the local venv runs and the test suite is green against.

FROM python:3.11-slim

# uid 1000 = HF Spaces' runtime user. Create it and own the dirs it writes.
RUN useradd --create-home --uid 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    CHROMA_PERSIST_DIR=/home/user/app/data/embeddings

WORKDIR /home/user/app

# 1) CPU-only torch FIRST, from the pytorch CPU index, so sentence-transformers
#    does not drag in the CUDA build. Separate layer = cached across rebuilds.
RUN pip install --no-cache-dir torch==2.13.0 \
      --index-url https://download.pytorch.org/whl/cpu

# 2) The exact-pinned heavy ML + server stack (PyPI). torch is already present,
#    so pip keeps it. One command so pip resolves them together, as installed.
RUN pip install --no-cache-dir \
      numpy==2.4.6 \
      scipy==1.17.1 \
      scikit-learn==1.9.0 \
      transformers==5.14.1 \
      tokenizers==0.22.2 \
      huggingface-hub==1.24.0 \
      safetensors==0.8.0 \
      sentence-transformers==5.6.0 \
      chromadb==1.5.9 \
      onnxruntime==1.27.0 \
      "uvicorn[standard]==0.51.0"

# 3) The application and its remaining (lighter) deps from pyproject. The heavy
#    deps above already satisfy the floors, so pip does not upgrade them.
COPY --chown=user:user . .
RUN pip install --no-cache-dir -e .

USER user

# Pre-download the embedder into the image as the runtime user, so it lands in a
# writable HF_HOME and the first cold-start request does not fetch it.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 7860

# HF probes the port; the app's own health route is /api/v1/health.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
