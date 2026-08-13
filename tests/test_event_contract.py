# Teste de contrato de eventos (schema)
import pytest
import json
import pathlib
import jsonschema

SCHEMAS_DIR = pathlib.Path(__file__).parent.parent / "core_dna"

# Exemplo de eventos válidos para teste
eventos = [
    {
        "type": "lead.created",
        "version": "v1",
        "payload": {"lead_id": "123", "name": "João", "email": "joao@exemplo.com"}
    },
    # Adicione outros exemplos conforme necessário
]

def load_schema(event_type, version):
    schema_path = SCHEMAS_DIR / f"{event_type}.{version}.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.parametrize("evento", eventos)
def test_event_schema(evento):
    schema = load_schema(evento["type"], evento["version"])
    jsonschema.validate(instance=evento["payload"], schema=schema)
