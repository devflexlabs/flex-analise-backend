"""
Configura o módulo backend antes dos imports.
Este arquivo deve ser importado antes de qualquer import de backend.*
"""
import sys
import importlib.util
from pathlib import Path

# Detecta a estrutura do projeto
script_path = Path(__file__).resolve()
script_dir = script_path.parent  # api/
root_dir = script_dir.parent      # raiz do projeto (onde estão extractors/, processors/, etc.)

# Verifica se o módulo backend já existe
if "backend" not in sys.modules:
    # Cria o módulo backend
    backend_module = type(sys)("backend")
    sys.modules["backend"] = backend_module
    
    # Adiciona a raiz ao path se ainda não estiver
    root_str = str(root_dir)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    
    # Cria os submódulos backend.extractors, backend.processors, backend.models
    for module_name in ["extractors", "processors", "models"]:
        module_dir = root_dir / module_name
        if module_dir.exists() and (module_dir / "__init__.py").exists():
            try:
                full_module_name = f"backend.{module_name}"
                if full_module_name not in sys.modules:
                    # Importa o módulo usando importlib
                    spec = importlib.util.spec_from_file_location(
                        full_module_name,
                        module_dir / "__init__.py"
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[full_module_name] = module
                        spec.loader.exec_module(module)
                        setattr(backend_module, module_name, module)
            except Exception:
                # Silenciosamente ignora erros de importação opcionais
                # (alguns módulos podem ter dependências opcionais)
                pass
