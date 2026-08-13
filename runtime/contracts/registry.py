from pydantic import BaseModel
from typing import Dict, Any, Type
import json

class ContractRegistry:
    """
    Centralized Contract Registry.
    Provides Pydantic schemas, Central OpenAPI spec generation, and versioning.
    """
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Type[BaseModel]]] = {}

    def register(self, module: str, version: str, name: str, schema: Type[BaseModel]):
        if module not in self._schemas:
            self._schemas[module] = {}
        target_name = f"{name}_v{version}"
        self._schemas[module][target_name] = schema
        
    def get_schema(self, module: str, version: str, name: str) -> Type[BaseModel]:
        target_name = f"{name}_v{version}"
        return self._schemas.get(module, {}).get(target_name)

    def generate_openapi(self) -> Dict[str, Any]:
        """
        Generates a unified OpenAPI specification containing all registered models.
        """
        openapi = {
            "openapi": "3.1.0",
            "info": {
                "title": "Civilization Central Contract Registry",
                "version": "1.0.0"
            },
            "components": {
                "schemas": {}
            }
        }
        
        for module, schemas in self._schemas.items():
            for name, schema_cls in schemas.items():
                schema_json = schema_cls.model_json_schema()
                openapi["components"]["schemas"][f"{module}.{name}"] = schema_json
                
        return openapi

registry = ContractRegistry()
