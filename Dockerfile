# --- Stage 1: Builder ---
FROM python:3.11-slim AS builder

# Install uv directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Force uv to use a specific venv path inside the container
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock ./

# Install dependencies into the venv (no-install-project skips copying app code yet)
RUN uv sync --frozen --no-install-project --no-dev

# --- Stage 2: Runtime ---
FROM python:3.11-slim

WORKDIR /app

# Set runtime env vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Add the venv's bin directory to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the venv from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy the rest of your application code
COPY . .

EXPOSE 8000

# Start the app using the venv's uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]