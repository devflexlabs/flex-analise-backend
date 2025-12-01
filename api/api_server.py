"""
API FastAPI para servir o extrator de contratos.
Pode ser consumida pela aplicação Next.js.
"""
# IMPORTANTE: Importa o setup do backend ANTES de qualquer import de backend.*
from ._setup_backend import *  # noqa: F401, F403

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da pasta config ou raiz
env_path = Path(__file__).parent.parent / "config" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from backend.extractors.contract_extractor_multiplo import ContractExtractorMultiplo
from backend.processors.document_processor import DocumentProcessor

app = FastAPI(title="Extrator de Contratos Financeiros API")

# Configura CORS para permitir requisições do Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://flex-analise.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o extrator (lazy loading)
_extractor = None
_doc_processor = None

def get_extractor():
    """Lazy loading do extrator."""
    global _extractor
    if _extractor is None:
        _extractor = ContractExtractorMultiplo(provider="auto")
    return _extractor

def get_doc_processor():
    """Lazy loading do processador de documentos."""
    global _doc_processor
    if _doc_processor is None:
        _doc_processor = DocumentProcessor(ocr_provider="auto")
    return _doc_processor

@app.get("/")
async def root():
    """Endpoint raiz."""
    return {"message": "Extrator de Contratos Financeiros API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}

@app.post("/api/extract")
async def extract_contract(file: UploadFile = File(...)):
    """
    Extrai informações de um contrato (PDF ou imagem).
    
    Args:
        file: Arquivo PDF ou imagem (JPEG/PNG)
        
    Returns:
        JSON com informações extraídas do contrato
    """
    # Valida tipo de arquivo
    valid_types = [
        "application/pdf",
        "image/jpeg",
        "image/jpg",
        "image/png",
    ]
    
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. Use PDF, JPEG ou PNG."
        )
    
    # Salva arquivo temporariamente
    temp_file = None
    try:
        # Cria arquivo temporário
        suffix = Path(file.filename).suffix if file.filename else ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Extrai informações
        extractor = get_extractor()
        doc_processor = get_doc_processor()
        
        # Processa o documento (PDF ou imagem)
        texto_extraido = doc_processor.process_document(file_path=temp_path)
        resultado = extractor.extract_from_text(texto_extraido)
        
        # Converte para dict
        return JSONResponse(content=resultado.model_dump())
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar contrato: {str(e)}"
        )
    finally:
        # Remove arquivo temporário
        if temp_file and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Adiciona o diretório raiz ao path para imports funcionarem
    root_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_dir))
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

