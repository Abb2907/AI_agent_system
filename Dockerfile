FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy project files and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi uvicorn openai python-dotenv httpx \
    sqlalchemy psycopg2-binary "python-jose[cryptography]" \
    "passlib[bcrypt]" slowapi alembic "pydantic[email]"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
