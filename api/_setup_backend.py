"""
Configura o módulo backend antes dos imports.
Este arquivo deve ser importado antes de qualquer import de backend.*
"""
import sys
import importlib.util
import importlib.machinery
from pathlib import Path

# Detecta a estrutura do projeto
script_path = Path(__file__).resolve()
script_dir = script_path.parent  # api/
root_dir = script_dir.parent      # raiz do projeto (onde estão extractors/, processors/, etc.)

# Cria um MetaPathFinder customizado para interceptar imports de backend.*
class BackendFinder:
    """Finder que intercepta imports de backend.* e redireciona para os diretórios corretos."""
    
    def __init__(self, root_path):
        self.root_path = Path(root_path)
    
    def find_spec(self, name, path, target=None):
        if name.startswith("backend."):
            parts = name.split(".")
            if len(parts) == 2:  # backend.extractors, backend.processors, etc.
                module_name = parts[1]
                module_dir = self.root_path / module_name
                if module_dir.exists() and (module_dir / "__init__.py").exists():
                    return importlib.util.spec_from_file_location(
                        name,
                        module_dir / "__init__.py",
                        submodule_search_locations=[str(module_dir)]
                    )
            elif len(parts) == 3:  # backend.extractors.contract_extractor_multiplo, etc.
                module_name = parts[1]
                submodule_name = parts[2]
                module_dir = self.root_path / module_name
                submodule_file = module_dir / f"{submodule_name}.py"
                if submodule_file.exists():
                    return importlib.util.spec_from_file_location(
                        name,
                        submodule_file,
                        submodule_search_locations=[str(module_dir)]
                    )
        return None

# Verifica se o módulo backend já existe
if "backend" not in sys.modules:
    # Adiciona a raiz ao path primeiro
    root_str = str(root_dir)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    
    # Adiciona o finder customizado ao meta_path
    if not any(isinstance(finder, BackendFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, BackendFinder(root_dir))
    
    # Cria o módulo backend
    backend_module = type(sys)("backend")
    sys.modules["backend"] = backend_module
    
    # Primeiro, cria módulos vazios para todos os submódulos
    # Isso evita erros de importação circular quando um módulo tenta importar outro
    modules_to_create = ["extractors", "processors", "models"]
    
    # Passo 1: Cria todos os módulos vazios primeiro
    for module_name in modules_to_create:
        module_dir = root_dir / module_name
        if module_dir.exists() and (module_dir / "__init__.py").exists():
            full_module_name = f"backend.{module_name}"
            if full_module_name not in sys.modules:
                # Cria um módulo vazio primeiro
                empty_module = type(sys)(full_module_name)
                sys.modules[full_module_name] = empty_module
                setattr(backend_module, module_name, empty_module)
    
    # Passo 2: Agora importa os módulos de verdade (agora que todos existem no sys.modules)
    # Importa na ordem: models, processors, extractors (para respeitar dependências)
    import_order = ["models", "processors", "extractors"]
    for module_name in import_order:
        module_dir = root_dir / module_name
        if module_dir.exists() and (module_dir / "__init__.py").exists():
            try:
                full_module_name = f"backend.{module_name}"
                # Tenta importar usando importlib.import_module primeiro
                # Isso funciona melhor com dependências entre módulos
                try:
                    module = importlib.import_module(full_module_name)
                    setattr(backend_module, module_name, module)
                except (ImportError, ModuleNotFoundError):
                    # Se import_module falhar, tenta com spec_from_file_location
                    spec = importlib.util.spec_from_file_location(
                        full_module_name,
                        module_dir / "__init__.py"
                    )
                    if spec and spec.loader:
                        # Substitui o módulo vazio pelo módulo real
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[full_module_name] = module
                        spec.loader.exec_module(module)
                        setattr(backend_module, module_name, module)
            except Exception as e:
                # Se falhar, mantém o módulo vazio
                # Isso permite que o código continue mesmo se houver dependências opcionais faltando
                pass
