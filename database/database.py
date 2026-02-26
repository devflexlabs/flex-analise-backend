"""
Configuração e gerenciamento do banco de dados.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Carrega .env
env_path = Path(__file__).parent.parent / "config" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Configuração do banco de dados
# Railway usa DATABASE_PUBLIC_URL, mas também aceita DATABASE_URL
# PostgreSQL é obrigatório - não usa SQLite
DATABASE_URL = os.getenv("DATABASE_PUBLIC_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL ou DATABASE_PUBLIC_URL deve estar configurado. "
        "PostgreSQL é obrigatório para este projeto."
    )

# Garante que é PostgreSQL
if not DATABASE_URL.startswith("postgresql://"):
    raise ValueError(
        f"Banco de dados deve ser PostgreSQL. URL recebida: {DATABASE_URL[:50]}..."
    )

# PostgreSQL - configuração otimizada
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    pool_size=5,  # Pool de conexões
    max_overflow=10,  # Conexões extras permitidas
    echo=False,  # Mude para True para ver SQL queries
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Inicializa o banco de dados PostgreSQL criando todas as tabelas."""
    from .models import Base
    
    try:
        # Dropa todas as tabelas existentes para recriar do zero
        Base.metadata.drop_all(bind=engine)
        print("[INFO] Tabelas antigas removidas")
    except Exception as e:
        print(f"[WARN] Erro ao remover tabelas antigas (pode nao existir): {e}")

    
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    print(f"[OK] Banco PostgreSQL inicializado: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")



def get_session() -> Session:
    """Retorna uma sessão do banco de dados."""
    return SessionLocal()


def get_db():
    """
    Generator para dependência do FastAPI.
    Use com Depends(get_db) nos endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

