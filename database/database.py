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
# Por padrão usa SQLite, mas pode ser configurado para PostgreSQL via variável de ambiente
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).parent.parent / 'analises_contratos.db'}"
)

# Se for SQLite, configura pool estático para permitir acesso concorrente
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Mude para True para ver SQL queries
    )
else:
    # PostgreSQL ou outro banco
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Inicializa o banco de dados criando todas as tabelas."""
    from .models import Base
    
    # Cria o diretório se não existir (para SQLite)
    if DATABASE_URL.startswith("sqlite"):
        db_path = Path(DATABASE_URL.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    print(f"✅ Banco de dados inicializado: {DATABASE_URL}")


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

