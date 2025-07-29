FROM python:3.11-bullseye
ARG AI_INSURANCE_CI_NAME

# Update system with security updates.
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY . /app
WORKDIR /app

# Configure uv to use Tsinghua mirror
ENV UV_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# Install dependencies using uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
RUN [ ! -e "ai_insurance_build.sh" ] || ./ai_insurance_build.sh

# Install OpenTelemetry auto-instrumentation.
RUN uv run opentelemetry-bootstrap -a install

# Create users.
RUN adduser --system --shell /usr/sbin/nologin --group --disabled-password --disabled-login --uid 2024 dev
RUN chmod -R =r,+X /app/*

RUN mkdir /python-cache && chown dev:dev /python-cache

USER dev
WORKDIR /app
RUN . .venv/bin/activate
RUN python -V

# Write .pyc files to a dedicated directory.
ENV PYTHONPYCACHEPREFIX=/python-pycache

# Enable auto-instrumentation for Python.
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

ENV AI_INSURANCE_CONTAINER_PORT=8080
ENV AI_INSURANCE_PYTHON_MODULE_NAME=main:app

CMD OTEL_PYTHON_LOG_LEVEL="$AI_INSURANCE_PYTHON_LOG_LEVEL" uv run opentelemetry-instrument \
    uvicorn "$AI_INSURANCE_PYTHON_MODULE_NAME" --host 0.0.0.0 --port "$AI_INSURANCE_CONTAINER_PORT"
