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
        # Garante que o módulo backend existe
        if "backend" not in sys.modules:
            backend_module = type(sys)("backend")
            sys.modules["backend"] = backend_module
        
        if name == "backend":
            # Retorna None para deixar o Python usar o módulo já criado
            return None
        
        if name.startswith("backend."):
            parts = name.split(".")
            if len(parts) == 2:  # backend.extractors, backend.processors, etc.
                module_name = parts[1]
                module_dir = self.root_path / module_name
                if module_dir.exists() and (module_dir / "__init__.py").exists():
                    # Garante que todos os módulos dependentes existem primeiro
                    # (extractors depende de processors, models e calculators)
                    if module_name == "extractors":
                        for dep_name in ["models", "processors", "calculators"]:
                            dep_module_name = f"backend.{dep_name}"
                            if dep_module_name not in sys.modules:
                                dep_dir = self.root_path / dep_name
                                if dep_dir.exists() and (dep_dir / "__init__.py").exists():
                                    dep_spec = importlib.util.spec_from_file_location(
                                        dep_module_name,
                                        dep_dir / "__init__.py",
                                        submodule_search_locations=[str(dep_dir)]
                                    )
                                    if dep_spec:
                                        if not dep_spec.loader:
                                            dep_spec.loader = importlib.machinery.SourceFileLoader(
                                                dep_module_name, str(dep_dir / "__init__.py")
                                            )
                                        try:
                                            dep_module = importlib.util.module_from_spec(dep_spec)
                                            # CRÍTICO: Define __path__ para que seja reconhecido como pacote
                                            dep_module.__path__ = [str(dep_dir)]
                                            dep_module.__package__ = dep_module_name
                                            sys.modules[dep_module_name] = dep_module
                                            dep_spec.loader.exec_module(dep_module)
                                            if "backend" in sys.modules:
                                                setattr(sys.modules["backend"], dep_name, dep_module)
                                        except Exception:
                                            pass
                    
                    spec = importlib.util.spec_from_file_location(
                        name,
                        module_dir / "__init__.py",
                        submodule_search_locations=[str(module_dir)]
                    )
                    if spec:
                        # Garante que o loader está configurado
                        if not spec.loader:
                            spec.loader = importlib.machinery.SourceFileLoader(name, str(module_dir / "__init__.py"))
                        # Se o módulo já existe mas não tem __path__, configura agora
                        if name in sys.modules:
                            existing_module = sys.modules[name]
                            if not hasattr(existing_module, '__path__'):
                                existing_module.__path__ = [str(module_dir)]
                                existing_module.__package__ = name
                        return spec
            elif len(parts) == 3:  # backend.extractors.contract_extractor_multiplo, etc.
                module_name = parts[1]
                submodule_name = parts[2]
                module_dir = self.root_path / module_name
                submodule_file = module_dir / f"{submodule_name}.py"
                if submodule_file.exists():
                    # Garante que o módulo pai existe primeiro
                    parent_module_name = f"backend.{module_name}"
                    if parent_module_name not in sys.modules:
                        # Cria o módulo pai se não existir
                        parent_spec = importlib.util.spec_from_file_location(
                            parent_module_name,
                            module_dir / "__init__.py",
                            submodule_search_locations=[str(module_dir)]
                        )
                        if parent_spec:
                            if not parent_spec.loader:
                                parent_spec.loader = importlib.machinery.SourceFileLoader(
                                    parent_module_name, str(module_dir / "__init__.py")
                                )
                            try:
                                parent_module = importlib.util.module_from_spec(parent_spec)
                                # CRÍTICO: Define __path__ para que seja reconhecido como pacote
                                parent_module.__path__ = [str(module_dir)]
                                parent_module.__package__ = parent_module_name
                                sys.modules[parent_module_name] = parent_module
                                parent_spec.loader.exec_module(parent_module)
                                if "backend" in sys.modules:
                                    setattr(sys.modules["backend"], module_name, parent_module)
                            except Exception:
                                pass  # Ignora erros ao criar módulo pai
                    else:
                        # Se o módulo já existe, garante que tem __path__ configurado
                        if parent_module_name in sys.modules:
                            parent_module = sys.modules[parent_module_name]
                            if not hasattr(parent_module, '__path__'):
                                parent_module.__path__ = [str(module_dir)]
                    
                    spec = importlib.util.spec_from_file_location(
                        name,
                        submodule_file,
                        submodule_search_locations=[str(module_dir)]
                    )
                    if spec:
                        # Garante que o loader está configurado
                        if not spec.loader:
                            spec.loader = importlib.machinery.SourceFileLoader(name, str(submodule_file))
                        return spec
        return None

# Sempre configura (mesmo se já existir, para garantir que funcione em processos filhos do uvicorn)
# Adiciona a raiz ao path primeiro
root_str = str(root_dir)
if root_str not in sys.path:
    sys.path.insert(0, root_str)

# Adiciona o finder customizado ao meta_path (sempre, para garantir que funcione em processos filhos)
backend_finder = None
for finder in sys.meta_path:
    if isinstance(finder, BackendFinder):
        backend_finder = finder
        break

if backend_finder is None:
    backend_finder = BackendFinder(root_dir)
    sys.meta_path.insert(0, backend_finder)

# Verifica se o módulo backend já existe
if "backend" not in sys.modules:
    # Cria o módulo backend
    backend_module = type(sys)("backend")
    sys.modules["backend"] = backend_module
    
    # Primeiro, cria módulos vazios para todos os submódulos
    # Isso evita erros de importação circular quando um módulo tenta importar outro
    modules_to_create = ["extractors", "processors", "models", "calculators"]
    
    # Passo 1: Cria todos os módulos vazios primeiro
    for module_name in modules_to_create:
        module_dir = root_dir / module_name
        if module_dir.exists() and (module_dir / "__init__.py").exists():
            full_module_name = f"backend.{module_name}"
            if full_module_name not in sys.modules:
                # Cria um módulo vazio primeiro
                empty_module = type(sys)(full_module_name)
                # CRÍTICO: Define __path__ para que seja reconhecido como pacote
                empty_module.__path__ = [str(module_dir)]
                empty_module.__package__ = full_module_name
                sys.modules[full_module_name] = empty_module
                setattr(backend_module, module_name, empty_module)
    
    # Passo 2: Agora importa os módulos de verdade (agora que todos existem no sys.modules)
    # Importa na ordem: models, processors, calculators, extractors (para respeitar dependências)
    import_order = ["models", "processors", "calculators", "extractors"]
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
                    if spec:
                        # Garante que o loader está configurado
                        if not spec.loader:
                            spec.loader = importlib.machinery.SourceFileLoader(
                                full_module_name,
                                str(module_dir / "__init__.py")
                            )
                        # Substitui o módulo vazio pelo módulo real
                        module = importlib.util.module_from_spec(spec)
                        # CRÍTICO: Define __path__ para que seja reconhecido como pacote
                        module.__path__ = [str(module_dir)]
                        module.__package__ = full_module_name
                        sys.modules[full_module_name] = module
                        spec.loader.exec_module(module)
                        setattr(backend_module, module_name, module)
            except Exception as e:
                # Se falhar, mantém o módulo vazio
                # Isso permite que o código continue mesmo se houver dependências opcionais faltando
                pass
