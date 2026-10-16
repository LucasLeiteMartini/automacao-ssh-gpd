FROM python:3.13-slim-bookworm

# Instala s3270 (suporte a terminal IBM TN3270 via py3270) e curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    s3270 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia o binário oficial do uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Otimizações de bytecode e variáveis de ambiente
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Cache de dependências do Python
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# Copia o código-fonte da aplicação
COPY src/ ./src/
COPY main.py ./

# Instala o projeto
RUN uv sync --frozen --no-dev

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "automacao.main:app", "--host", "0.0.0.0", "--port", "8000"]
