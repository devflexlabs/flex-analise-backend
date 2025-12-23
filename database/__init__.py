"""
Módulo de banco de dados para armazenamento de análises de contratos.
"""
import sys
from pathlib import Path

# Obtém o diretório atual do módulo
_current_dir = Path(__file__).parent

# Adiciona o diretório pai ao path se necessário para imports
_parent_dir = _current_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# Importa os módulos - tenta import relativo primeiro, depois absoluto
try:
    # Tenta import relativo (funciona quando carregado como pacote)
    from .database import get_db, init_db, get_session
    from .models import AnaliseContrato
except (ImportError, ValueError, SystemError):
    # Se falhar, tenta import absoluto
    try:
        from backend.database.database import get_db, init_db, get_session
        from backend.database.models import AnaliseContrato
    except ImportError:
        # Último recurso: importa diretamente dos arquivos
        import importlib.util
        
        database_path = _current_dir / "database.py"
        models_path = _current_dir / "models.py"
        
        if database_path.exists():
            spec = importlib.util.spec_from_file_location("database.database", database_path)
            if spec and spec.loader:
                database_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(database_module)
                get_db = database_module.get_db
                init_db = database_module.init_db
                get_session = database_module.get_session
        
        if models_path.exists():
            spec = importlib.util.spec_from_file_location("database.models", models_path)
            if spec and spec.loader:
                models_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(models_module)
                AnaliseContrato = models_module.AnaliseContrato

__all__ = ["get_db", "init_db", "get_session", "AnaliseContrato"]

