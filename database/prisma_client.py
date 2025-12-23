"""
Cliente Prisma para acesso ao banco de dados.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona o caminho do Prisma Client gerado ao sys.path
_prisma_client_path = Path(__file__).parent.parent / "node_modules" / ".prisma" / "client"
if _prisma_client_path.exists() and str(_prisma_client_path.parent) not in sys.path:
    sys.path.insert(0, str(_prisma_client_path.parent))

# Importa Prisma do cliente gerado
try:
    # Tenta importar do cliente gerado pelo Prisma
    from prisma import Prisma
    from prisma.models import AnaliseContrato
except ImportError:
    # Se falhar, tenta importar diretamente do caminho gerado
    try:
        import importlib.util
        prisma_module_path = _prisma_client_path / "index.py"
        if prisma_module_path.exists():
            spec = importlib.util.spec_from_file_location("prisma", prisma_module_path)
            if spec and spec.loader:
                prisma_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(prisma_module)
                Prisma = prisma_module.Prisma
                AnaliseContrato = prisma_module.models.AnaliseContrato
        else:
            raise ImportError("Prisma Client não encontrado. Execute 'npx prisma generate'")
    except Exception as e:
        raise ImportError(
            f"Prisma Client não encontrado. Execute 'npx prisma generate' para gerar o cliente. Erro: {e}"
        )

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

