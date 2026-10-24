FROM python:3.13-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /bin/uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

RUN mkdir -p /app/certs && curl --fail --silent --show-error \
    https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem \
    --output /app/certs/rds-ca.pem

FROM base AS test
RUN uv sync --frozen
COPY tests ./tests
CMD ["uv", "run", "pytest", "-q"]

FROM base AS runtime
RUN useradd --uid 10001 --create-home appuser
USER appuser

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
