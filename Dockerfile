# Stage 1: Build virtual environment with dependencies
FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --target=/app/deps \
    "starlette>=0.41" \
    "uvicorn[standard]>=0.32" \
    "jinja2>=3.1" \
    "itsdangerous>=2.2" \
    "python-multipart>=0.0.12"

# Stage 2: Production image
FROM python:3.12-slim

RUN useradd --create-home --shell /bin/bash caspyan

COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/
COPY src/ /app/src/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

USER caspyan
WORKDIR /app

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "caspyan.app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
