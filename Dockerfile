# Dockerfile for Hugging Face Spaces deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy model directly (avoids runtime download)
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.7.1/en_core_web_lg-3.7.1-py3-none-any.whl

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

# Run the application with unbuffered output
CMD ["streamlit", "run", "multi_agent_demo/guards_demo_ui.py", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
