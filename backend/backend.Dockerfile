FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by Python packages and the app
# (psycopg needs libpq, pymupdf/pillow need libjpeg, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    libjpeg-dev \
    zlib1g-dev \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# ──────────────────────────────────────────────────────────────
# STAGE 1: Core serving packages — everything the app needs to
# START and serve claims + fraud detection.  Derived from a full
# AST scan of every import in backend/app/.
#
# Heavy training-only / RAG packages (faiss-cpu, ctgan, tgan,
# sentence-transformers, mlflow, weasyprint) are intentionally
# EXCLUDED — they are lazily imported with try/except fallbacks,
# so the app boots fine without them.  Those features (model
# retraining, RAG knowledge search) simply report "unavailable".
# ──────────────────────────────────────────────────────────────
RUN uv pip install --system --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    pydantic \
    pydantic-settings \
    psycopg[binary] \
    python-dotenv \
    alembic \
    pandas \
    scikit-learn \
    joblib \
    "numpy<2" \
    shap==0.45.0 \
    lightgbm \
    xgboost \
    imbalanced-learn \
    pymupdf==1.24.7 \
    python-docx==1.1.2 \
    python-jose[cryptography] \
    passlib[bcrypt] \
    bcrypt \
    python-multipart \
    email-validator \
    pyotp \
    slowapi \
    qrcode \
    redis==5.0.1 \
    langchain-groq==0.1.6 \
    pyyaml==6.0.1 \
    optuna \
    Pillow \
    langchain-core \
    langgraph==0.1.8

# ──────────────────────────────────────────────────────────────
# STAGE 2: Optional packages used by specific features.
# If any fail the app still boots.
# ──────────────────────────────────────────────────────────────
RUN uv pip install --system --no-cache-dir \
    psutil \
    matplotlib \
    seaborn \
    tiktoken==0.7.0 \
    markdown==3.6 \
    beautifulsoup4==4.12.3 \
    langchain-google-genai \
    langgraph-checkpoint-postgres==1.0.4 \
    pytesseract \
    || echo "WARNING: Some optional packages failed to install — app will still start"

# Copy source code
COPY . .

# Environment variables
ENV PYTHONPATH=/app
ENV ENV=production

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
