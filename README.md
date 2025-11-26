# Flex Análise - Backend API

API Python para extração e análise inteligente de informações de contratos financeiros usando múltiplos provedores de IA.

## 🚀 Tecnologias

- **FastAPI** - Framework web moderno e rápido
- **LangChain** - Orquestração de LLMs
- **Pydantic** - Validação de dados
- **PyPDF2 / pdfplumber** - Extração de texto de PDFs
- **Tesseract / EasyOCR** - OCR para imagens
- **Python 3.10+**

## 📋 Pré-requisitos

- Python 3.10 ou superior
- pip
- Tesseract OCR (opcional, para OCR local)

## 🛠️ Instalação

```bash
# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

1. Copie o arquivo `.env.example` para `.env` (se existir) ou crie um arquivo `.env` na pasta `config/`:

```env
# Provedores de IA (escolha um ou mais)
OPENAI_API_KEY=sua_chave_openai
GROQ_API_KEY=sua_chave_groq
GOOGLE_API_KEY=sua_chave_google_gemini
OLLAMA_BASE_URL=http://localhost:11434

# Configurações
IA_PROVIDER=auto  # auto, openai, groq, gemini, ollama
OCR_PROVIDER=auto  # auto, tesseract, easyocr, google, aws
```

2. Para usar Ollama (local), instale e inicie o serviço:
```bash
# Instalar Ollama: https://ollama.ai
ollama serve
```

## 🚀 Executando a API

### Opção 1: Script de inicialização (Windows)
```bash
scripts\iniciar_api.bat
```

### Opção 2: Script de inicialização (Linux/Mac)
```bash
chmod +x scripts/iniciar_api.sh
./scripts/iniciar_api.sh
```

### Opção 3: Executar diretamente
```bash
python backend/api/run_api.py
```

A API estará disponível em `http://localhost:8000`

## 📡 Endpoints

### POST `/api/extract`

Extrai informações de um contrato financeiro (PDF ou imagem).

**Request:**
- Content-Type: `multipart/form-data`
- Body: arquivo PDF, JPEG ou PNG

**Response:**
```json
{
  "nome_cliente": "Nome do Cliente",
  "cpf_cnpj": "000.000.000-00",
  "numero_contrato": "123456",
  "tipo_contrato": "Financiamento",
  "valor_divida": 50000.00,
  "quantidade_parcelas": 36,
  "valor_parcela": 1500.00,
  "taxa_juros": 2.5,
  "data_vencimento_primeira": "2025-02-01",
  "data_vencimento_ultima": "2028-01-01",
  "observacoes": "Análise detalhada do contrato..."
}
```

## 🧠 Provedores de IA Suportados

- **OpenAI** - GPT-4, GPT-3.5
- **Groq** - Mixtral, Llama (gratuito com limites)
- **Google Gemini** - Gemini Pro, Gemini Flash
- **Ollama** - Modelos locais (Llama, Mistral, etc.)

O sistema escolhe automaticamente o melhor provedor disponível quando `IA_PROVIDER=auto`.

## 📄 Processamento de Documentos

### PDFs
- Extração de texto usando PyPDF2 e pdfplumber
- Suporte para PDFs com texto e PDFs escaneados (requer OCR)

### Imagens (JPEG, PNG)
- OCR usando Tesseract, EasyOCR ou Google Vision API
- Detecção automática de texto em imagens

## 📁 Estrutura do Projeto

```
backend/
├── api/
│   ├── api_server.py      # Servidor FastAPI principal
│   └── run_api.py         # Script de inicialização
├── extractors/
│   └── contract_extractor_multiplo.py  # Extrator com múltiplos provedores
├── processors/
│   ├── document_processor.py  # Processamento de PDFs/imagens
│   └── ocr_provider.py        # Provedores de OCR
├── models/
│   └── models.py          # Modelos Pydantic
├── apps/
│   └── streamlit/
│       └── app.py         # Interface Streamlit (opcional)
├── scripts/
│   ├── iniciar_api.bat    # Script Windows
│   └── iniciar_api.sh     # Script Linux/Mac
└── requirements.txt
```

## 🔍 Funcionalidades

- ✅ Extração automática de informações de contratos
- ✅ Suporte para múltiplos provedores de IA
- ✅ OCR para PDFs escaneados e imagens
- ✅ Análise de cláusulas abusivas e irregularidades
- ✅ Validação de dados com Pydantic
- ✅ API RESTful com FastAPI
- ✅ CORS configurado para frontend

## 🛡️ Análise de Irregularidades

O sistema identifica automaticamente:
- Taxas de juros abusivas
- Cláusulas abusivas segundo CDC/BACEN
- Não conformidades regulatórias
- Informações críticas do contrato

## 📝 Documentação da API

Com a API rodando, acesse:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Desenvolvimento

```bash
# Executar com reload automático
uvicorn backend.api.api_server:app --reload --host 0.0.0.0 --port 8000
```

## 📄 Licença

Proprietário - Grupo Flex

