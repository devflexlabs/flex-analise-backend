"""
Módulo de banco de dados para armazenamento de análises de contratos.
"""
# Importa diretamente dos módulos - mais confiável com carregamento dinâmico
try:
    # Tenta import relativo primeiro (funciona quando carregado como pacote normal)
    from . import database as _database_module
    from . import models as _models_module
except (ImportError, ValueError, SystemError, AttributeError):
    # Se falhar, importa diretamente dos arquivos usando importlib
    import importlib.util
    import sys
    from pathlib import Path
    
    _current_dir = Path(__file__).parent
    _parent_dir = _current_dir.parent
    
    # Adiciona ao path se necessário
    if str(_parent_dir) not in sys.path:
        sys.path.insert(0, str(_parent_dir))
    
    # Carrega database.py
    database_path = _current_dir / "database.py"
    if database_path.exists():
        spec = importlib.util.spec_from_file_location("backend.database.database", database_path)
        if spec and spec.loader:
            _database_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_database_module)
    
    # Carrega models.py
    models_path = _current_dir / "models.py"
    if models_path.exists():
        spec = importlib.util.spec_from_file_location("backend.database.models", models_path)
        if spec and spec.loader:
            _models_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_models_module)

# Exporta as funções e classes
get_db = _database_module.get_db
init_db = _database_module.init_db
get_session = _database_module.get_session
AnaliseContrato = _models_module.AnaliseContrato

__all__ = ["get_db", "init_db", "get_session", "AnaliseContrato"]

