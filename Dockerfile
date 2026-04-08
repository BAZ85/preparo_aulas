FROM python:3.11-slim
WORKDIR /app

# Instala pacote essencial do sistema Linux para exportação DOCX (Pypandoc)
RUN apt-get update && apt-get install -y pandoc && rm -rf /var/lib/apt/lists/*

# Instala via binário super-leve do uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copia configurações vitais para a Inteligência do backend
COPY pyproject.toml uv.lock ./

# Usamos as opções nativas do uv para instalar no sistema do container sem virtualenv
# A flag '--system' é a recomendação nativa para imagens Docker 
RUN uv pip install --system -r pyproject.toml || uv pip install --system -e . || pip install -r pyproject.toml

# Puxa o código central da máquina python
COPY src/ ./src/

EXPOSE 8000

# Execução nativa para uso assíncrono via WSGI
CMD ["uvicorn", "src.preparo_de_aula.api:app", "--host", "0.0.0.0", "--port", "8000"]
