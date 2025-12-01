"""
Script wrapper para executar a API.
Facilita a execução mantendo o diretório raiz no path.
Funciona tanto no projeto original quanto no repositório clonado.
"""
import sys
from pathlib import Path
import os
import importlib.util
import importlib.machinery

# Detecta a estrutura do projeto
script_path = Path(__file__).resolve()
script_dir = script_path.parent
current_dir = Path.cwd().resolve()

# Detecta se estamos no repositório clonado (estrutura plana) ou projeto original
# Repositório clonado: api/run_api.py na raiz, com extractors/ na mesma raiz (NÃO dentro de pasta backend)
is_cloned_repo = (
    script_dir.name == "api" 
    and (script_dir.parent / "extractors").exists() 
    and script_dir.parent.name != "backend"  # Não está dentro de uma pasta backend
)

# Projeto original: backend/api/run_api.py, com backend/extractors/ na raiz do projeto
is_original_repo = (
    script_dir.parent.name == "backend" 
    and (script_dir.parent / "extractors").exists()
)

if is_cloned_repo:
    # Repositório clonado: estrutura plana (api/, extractors/, etc. na raiz)
    root_dir = script_dir.parent
    app_import = "api.api_server:app"
    sys.path.insert(0, str(root_dir))
    
elif is_original_repo:
    # Projeto original: estrutura com pasta backend (backend/api/, backend/extractors/, etc.)
    root_dir = script_dir.parent.parent
    app_import = "backend.api.api_server:app"
    sys.path.insert(0, str(root_dir))
    
else:
    # Fallback: detecta automaticamente a partir do diretório atual
    root_dir = current_dir
    if (root_dir / "backend" / "api" / "api_server.py").exists():
        app_import = "backend.api.api_server:app"
        sys.path.insert(0, str(root_dir))
    elif (root_dir / "api" / "api_server.py").exists():
        # Repositório clonado
        root_dir = root_dir
        app_import = "api.api_server:app"
        sys.path.insert(0, str(root_dir))
    else:
        raise RuntimeError(
            f"Não foi possível encontrar api_server.py.\n"
            f"Script: {script_path}\n"
            f"Diretório atual: {current_dir}\n"
            f"Execute a partir da raiz do projeto."
        )

# Muda o diretório de trabalho para a raiz
os.chdir(root_dir)

print(f"✓ Executando API a partir de: {root_dir}")
print(f"✓ Importando: {app_import}")

# Importa e executa a API
if __name__ == "__main__":
    import uvicorn
    
    # Importa o setup_backend PRIMEIRO para configurar os módulos backend
    # Isso deve ser feito antes de qualquer import de api_server
    if is_cloned_repo or (not is_original_repo and (root_dir / "api" / "api_server.py").exists()):
        # Para estrutura plana, importa diretamente
        from api._setup_backend import *  # noqa: F401, F403
        from api.api_server import app
    else:
        # Para estrutura com backend/
        from backend.api._setup_backend import *  # noqa: F401, F403
        from backend.api.api_server import app
    
    # Desabilita reload para evitar problemas com imports em processos filhos
    # Use --reload na linha de comando se precisar de hot reload
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
