# Backend image (Docker-based hosts; written for HF Spaces, works anywhere the
# platform expects a plain Dockerfile).
#
# Baked in:
#   - listens on port 7860 (HF's expected app port; harmless elsewhere)
#   - runs as uid 1000 (HF Spaces' non-root user) with writable cache dirs
#   - fastembed (ONNX) embedder — NOT torch. The torch build held ~370 MB
#     resident and peaked ~683 MB on the first knowledge search; the ONNX build
#     of the same MiniLM model fits free-tier 512 MB ceilings (2026-07-23 swap).
#   - the MiniLM ONNX model is pre-downloaded into the image, so the first
#     request after a cold start does not pay the download
#
# Exact pins for the load-bearing / heavy stack: hosts rebuild the image
# remotely, so `>=`/`~=` could silently drift to an untested patch. These
# versions are the exact set the local venv runs and the test suite is green
# against.

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

# 1) The exact-pinned heavy stack (no torch — fastembed serves MiniLM via
#    onnxruntime). One command so pip resolves them together, as installed.
RUN pip install --no-cache-dir \
      numpy==2.4.6 \
      huggingface-hub==1.24.0 \
      tokenizers==0.22.2 \
      onnxruntime==1.27.0 \
      fastembed==0.8.0 \
      chromadb==1.5.9 \
      "uvicorn[standard]==0.51.0"

# 2) The application and its remaining (lighter) deps from pyproject. The heavy
#    deps above already satisfy the floors, so pip does not upgrade them.
COPY --chown=user:user . .
RUN pip install --no-cache-dir -e .

USER user

# Pre-download the ONNX embedder into the image as the runtime user, so it
# lands in a writable cache and the first cold-start request does not fetch it.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 7860

# HF probes the port; the app's own health route is /api/v1/health.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
