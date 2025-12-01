FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Atualiza pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copia requirements e instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY . .

# Configura PYTHONPATH
ENV PYTHONPATH=/app

# Expõe a porta
EXPOSE 8000

# Usa uvicorn diretamente com o app FastAPI
# O _setup_backend.py será importado automaticamente pelo api_server.py
# Usa PORT da variável de ambiente (Railway) ou 8000 como padrão
CMD sh -c "uvicorn api.api_server:app --host 0.0.0.0 --port \${PORT:-8000}"
