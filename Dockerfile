# Use an official Python runtime with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install system dependencies for Manim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    pkg-config \
    libpangocairo-1.0-0 \
    libcairo2-dev \
    libpango1.0-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy dependency configuration files
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen --no-install-project

# Copy the rest of the application code
COPY . .

# Expose port 8000 (Google Cloud Run will override this with PORT env variable, but good for local/defaults)
EXPOSE 8000

# Set default environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV RELOAD=false

# Start the FastAPI server using uv run to execute in the sync'd environment
CMD ["uv", "run", "python", "main.py"]
