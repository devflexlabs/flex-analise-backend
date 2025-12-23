"""
API FastAPI para servir o extrator de contratos.
Pode ser consumida pela aplicação Next.js.
"""
# IMPORTANTE: Importa o setup do backend ANTES de qualquer import de backend.*
from ._setup_backend import *  # noqa: F401, F403

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Carrega .env da pasta config ou raiz
env_path = Path(__file__).parent.parent / "config" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from backend.extractors.contract_extractor_multiplo import ContractExtractorMultiplo
from backend.processors.document_processor import DocumentProcessor

# Importa módulo de banco de dados usando SQLAlchemy
from backend.database.database import init_db, get_db, get_session
from backend.database.repository import AnaliseRepository

app = FastAPI(title="Extrator de Contratos Financeiros API")

# Inicializa banco de dados na startup
@app.on_event("startup")
async def startup_event():
    """Inicializa o banco de dados na inicialização da API."""
    try:
        init_db()
        print("✅ Banco de dados inicializado com sucesso")
    except Exception as e:
        print(f"⚠️  Erro ao inicializar banco de dados: {e}")

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


# ==================== ENDPOINTS DE RELATÓRIOS ====================

@app.get("/api/relatorios/estatisticas-banco")
async def estatisticas_por_banco(
    estado: Optional[str] = Query(None, description="Filtrar por estado (ex: RS)"),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas agregadas por banco.
    
    Inclui:
    - Total de contratos por banco
    - Taxa média de juros por banco
    - Valor médio e total de dívidas
    - Total de veículos financiados
    - Percentual de contratos com taxa abusiva
    """
    try:
        repository = AnaliseRepository(db)
        resultado = repository.estatisticas_por_banco(estado=estado)
        # Garante que sempre retorna uma lista, mesmo se vazia
        return resultado if resultado else []
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas por banco: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar estatísticas: {str(e)}"
        )


@app.get("/api/relatorios/estatisticas-produto")
async def estatisticas_por_produto(
    estado: Optional[str] = Query(None, description="Filtrar por estado (ex: RS)"),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas agregadas por tipo de produto (empréstimo, financiamento, etc.).
    """
    repository = AnaliseRepository(db)
    return repository.estatisticas_por_produto(estado=estado)


@app.get("/api/relatorios/mapa-divida")
async def mapa_divida(
    ano: int = Query(..., description="Ano do relatório (ex: 2024)"),
    mes: int = Query(..., description="Mês do relatório (1-12)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ex: RS)"),
    db: Session = Depends(get_db)
):
    """
    Gera relatório mensal tipo "mapa da dívida".
    
    Retorna:
    - Resumo geral (total de análises, taxas médias, valores)
    - Top bancos por taxa de juros
    - Bancos que mais apreendem veículos
    - Distribuição por estado
    - Distribuição por faixa etária
    """
    if mes < 1 or mes > 12:
        raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
    
    repository = AnaliseRepository(db)
    return repository.mapa_divida_mensal(ano=ano, mes=mes, estado=estado)


@app.get("/api/relatorios/analises")
async def listar_analises(
    limite: int = Query(100, ge=1, le=1000, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    banco: Optional[str] = Query(None, description="Filtrar por banco"),
    tipo_contrato: Optional[str] = Query(None, description="Filtrar por tipo de contrato"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db)
):
    """
    Lista análises de contratos com filtros opcionais.
    """
    repository = AnaliseRepository(db)
    analises = repository.listar_analises(
        limite=limite,
        offset=offset,
        banco=banco,
        tipo_contrato=tipo_contrato,
        estado=estado
    )
    return [analise.to_dict() for analise in analises]


@app.get("/api/relatorios/analise/{analise_id}")
async def obter_analise(
    analise_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém uma análise específica por ID.
    """
    repository = AnaliseRepository(db)
    analise = repository.obter_por_id(analise_id)
    
    if not analise:
        raise HTTPException(status_code=404, detail="Análise não encontrada")
    
    return analise.to_dict()

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
        
        # Salva automaticamente no banco de dados (só se não for duplicado)
        analise_salva = None
        ja_existia = False
        try:
            db = get_session()
            repository = AnaliseRepository(db)
            # Verifica se já existe antes de salvar
            existing = repository.verificar_duplicado(resultado)
            if existing:
                analise_salva = existing
                ja_existia = True
                print(f"ℹ️  Contrato já existe no banco (ID: {analise_salva.id}). Não salvando duplicado.")
            else:
                # Debug: mostra o que está sendo salvo
                print(f"📝 Salvando análise no banco:")
                print(f"   - Veículo: {resultado.veiculo_marca} {resultado.veiculo_modelo} {resultado.veiculo_ano}")
                print(f"   - Placa: {resultado.veiculo_placa}, RENAVAM: {resultado.veiculo_renavam}")
                print(f"   - Observações: {len(resultado.observacoes or '')} caracteres")
                
                analise_salva = repository.salvar_analise(
                    contrato_info=resultado,
                    arquivo_original=file.filename
                )
                if analise_salva:
                    db.commit()
                    print(f"✅ Análise salva no banco de dados: ID {analise_salva.id}")
                    print(f"   - Veículo salvo: {analise_salva.veiculo_marca} {analise_salva.veiculo_modelo}")
                    print(f"   - Observações salvas: {len(analise_salva.observacoes or '')} caracteres")
            db.close()
        except Exception as db_error:
            # Loga erro mas não falha a requisição
            print(f"⚠️  Erro ao salvar análise no banco: {db_error}")
            import traceback
            traceback.print_exc()
            if 'db' in locals():
                db.rollback()
                db.close()
        
        # Converte para dict
        resultado_dict = resultado.model_dump()
        resultado_dict["analise_id"] = analise_salva.id if analise_salva else None
        resultado_dict["ja_existia"] = ja_existia
        
        return JSONResponse(content=resultado_dict)
        
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

