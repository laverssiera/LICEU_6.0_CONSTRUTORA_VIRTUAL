# Plugin Loader para carregamento dinâmico de módulos
import importlib
import pkgutil
from typing import Dict, Any

def load_plugins(path: str) -> Dict[str, Any]:
    modules = {}
    for finder, name, ispkg in pkgutil.iter_modules([path]):
        try:
            module = importlib.import_module(f"runtime.{name}")
            modules[name] = module
        except Exception as e:
            print(f"[PluginLoader] Falha ao carregar módulo {name}: {e}")
    return modules
