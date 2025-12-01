FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para OCR e processamento de PDFs
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do backend
COPY . .

# Configura PYTHONPATH para que o Python encontre os módulos backend
# A Railway executa na raiz do projeto, então precisamos adicionar o diretório atual ao PYTHONPATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Expõe a porta (Railway vai definir a variável PORT)
EXPOSE 8000

# Comando para iniciar a aplicação
# Usa o script run_api.py que já faz o setup correto do path
CMD ["python", "-m", "backend.api.run_api"]

