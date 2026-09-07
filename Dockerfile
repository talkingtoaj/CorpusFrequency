# Multi-stage: the build stage carries uv and the toolchain, the runtime
# stage carries only the interpreter, the venv and the app.
FROM python:3.14-slim AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, so a source-only change does not invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN uv sync --locked --no-dev


FROM python:3.14-slim AS runtime

# nltk's tokeniser data would otherwise be downloaded on first request, into
# a home directory the non-root user may not own. Baked in at build time.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    NLTK_DATA=/usr/share/nltk_data

WORKDIR /app

COPY --from=build /app /app

RUN python -m nltk.downloader -d /usr/share/nltk_data punkt_tab \
    && useradd --create-home --uid 1000 app \
    && chown -R app:app /app

USER app

# Collected here rather than at startup: the filesystem is read-only at run
# time, and every cold start would otherwise repeat the work.
RUN DJANGO_SECRET_KEY=build-time-only \
    DJANGO_DEBUG=0 \
    DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

EXPOSE 8080

# Cloud Run sets PORT. One worker per container, scaled by Cloud Run itself;
# threads absorb the I/O wait on database and static reads.
CMD exec gunicorn config.wsgi:application \
    --bind :${PORT:-8080} \
    --workers 1 \
    --threads 8 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
