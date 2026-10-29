FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv==0.13.6
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY warehouse ./warehouse
COPY analyses ./analyses
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" ATLAS_DATA_DIR=/data
EXPOSE 8020
CMD ["atlasiq","serve","--port","8020"]
