"""
Cliente Prisma para acesso ao banco de dados.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from prisma import Prisma
from prisma.models import AnaliseContrato

# Carrega .env
env_path = Path(__file__).parent.parent / "config" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Configuração do banco de dados
# Railway usa DATABASE_PUBLIC_URL, mas Prisma espera DATABASE_URL
database_public_url = os.getenv("DATABASE_PUBLIC_URL")
database_url = os.getenv("DATABASE_URL")

# Prisma usa DATABASE_URL, então definimos se DATABASE_PUBLIC_URL estiver disponível
if database_public_url and not database_url:
    os.environ["DATABASE_URL"] = database_public_url

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL ou DATABASE_PUBLIC_URL deve estar configurado. "
        "Configure no Railway ou no arquivo .env"
    )

# Inicializa cliente Prisma
# Prisma lê DATABASE_URL do ambiente automaticamente
prisma = Prisma()


async def init_db():
    """Inicializa o banco de dados criando todas as tabelas."""
    await prisma.connect()
    # Prisma cria as tabelas automaticamente via migrations
    print(f"✅ Banco de dados conectado: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")


async def disconnect_db():
    """Desconecta do banco de dados."""
    await prisma.disconnect()

