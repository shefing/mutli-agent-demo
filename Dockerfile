# Dockerfile for Hugging Face Spaces deployment
# Build cache invalidation: 2025-10-16-v7-fix-permissions
# Using CPU-only PyTorch to save ~5GB
# Fixed: Use /tmp for writable storage on HF Spaces
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and clean up in same layer
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install NumPy first with specific version to avoid binary incompatibility
RUN pip install --no-cache-dir "numpy>=2.1.1,<3.0.0"

# Install PyTorch CPU-only version first (much smaller than CUDA version)
# This saves ~5GB by avoiding CUDA dependencies
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install Python dependencies
# Clean pip cache and remove unnecessary files to save space
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip cache purge \
    && rm -rf /root/.cache/pip \
    && find /usr/local/lib/python3.11 -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -type d -name "tests" -exec rm -r {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.11 -type f -name "*.pyc" -delete \
    && find /usr/local/lib/python3.11 -type f -name "*.pyo" -delete \
    && find /usr/local/lib/python3.11 -type f -name "*.whl" -delete

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Disable Python output buffering to see logs immediately
ENV PYTHONUNBUFFERED=1

# Start Streamlit with the new multi-page app
CMD streamlit run multi_agent_demo/app.py --server.enableCORS=false --server.enableXsrfProtection=false
