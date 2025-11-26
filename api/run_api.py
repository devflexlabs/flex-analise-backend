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
    
    # Cria módulo "backend" dinâmico para que os imports "from backend.xxx" funcionem
    # Os módulos estão diretamente na raiz, mas api_server.py espera "backend.xxx"
    backend_module = type(sys)("backend")
    sys.modules["backend"] = backend_module
    
    # Adiciona os submódulos ao módulo backend
    # Primeiro adiciona a raiz ao path para que os imports funcionem
    sys.path.insert(0, str(root_dir))
    
    for module_name in ["extractors", "processors", "models"]:
        module_dir = root_dir / module_name
        if module_dir.exists():
            # Importa usando importlib para criar o namespace backend.xxx
            try:
                # Tenta importar diretamente primeiro
                full_module_name = f"backend.{module_name}"
                if full_module_name not in sys.modules:
                    # Cria um loader que aponta para o módulo na raiz
                    loader = importlib.machinery.SourceFileLoader(
                        full_module_name,
                        str(module_dir / "__init__.py") if (module_dir / "__init__.py").exists() else str(module_dir)
                    )
                    module = loader.load_module()
                    sys.modules[full_module_name] = module
                    setattr(backend_module, module_name, module)
            except Exception as e:
                print(f"Aviso: Não foi possível carregar backend.{module_name}: {e}")
    
    # Adiciona a raiz ao path
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
        # Cria módulo backend dinâmico
        backend_module = type(sys)("backend")
        sys.modules["backend"] = backend_module
        sys.path.insert(0, str(root_dir))
        for module_name in ["extractors", "processors", "models"]:
            module_dir = root_dir / module_name
            if module_dir.exists():
                try:
                    full_module_name = f"backend.{module_name}"
                    if full_module_name not in sys.modules:
                        loader = importlib.machinery.SourceFileLoader(
                            full_module_name,
                            str(module_dir / "__init__.py") if (module_dir / "__init__.py").exists() else str(module_dir)
                        )
                        module = loader.load_module()
                        sys.modules[full_module_name] = module
                        setattr(backend_module, module_name, module)
                except Exception as e:
                    print(f"Aviso: Não foi possível carregar backend.{module_name}: {e}")
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
    uvicorn.run(app_import, host="0.0.0.0", port=8000, reload=True)
