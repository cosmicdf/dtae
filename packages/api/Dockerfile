FROM python:3.11-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY packages/core /build/core
RUN uv pip install /build/core --system --no-cache

COPY packages/api/pyproject.toml .
COPY packages/api/app ./app
RUN uv pip install . --system --no-cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
