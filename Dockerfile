FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md LICENSE requirements.lock ./
COPY src ./src
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.lock \
    && /opt/venv/bin/pip install --no-cache-dir --no-deps --no-build-isolation .

FROM python:3.12-slim
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY --chown=appuser:appuser src ./src
ENV PATH="/opt/venv/bin:$PATH" PYTHONPATH=/app/src LEARNING_PLANE_EVIDENCE=/app/evidence
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "learning_plane.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

