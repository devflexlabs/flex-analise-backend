FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para OCR e processamento de PDFs
# Usa --no-install-recommends para reduzir tamanho e tempo
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Atualiza pip, setuptools e wheel (cache separado)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copia apenas requirements.txt primeiro para aproveitar cache do Docker
# Se requirements.txt não mudar, esta camada será reutilizada
COPY requirements.txt .

# Instala dependências Python (esta camada será cacheada se requirements.txt não mudar)
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código (último para não invalidar cache das dependências)
COPY . .

# Configura PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Expõe a porta
EXPOSE 8000

# Comando para iniciar
CMD ["python", "-m", "backend.api.run_api"]

