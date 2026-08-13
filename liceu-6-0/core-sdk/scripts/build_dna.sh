#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOOTSTRAP_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${BOOTSTRAP_ROOT}/.." && pwd)"
PROTO_SRC="${BOOTSTRAP_ROOT}/core_dna"
LEGACY_PROTO_SRC="${REPO_ROOT}/core_dna"
PY_OUT_DIR="${BOOTSTRAP_ROOT}/core-sdk/generated/python"
TS_OUT_DIR="${BOOTSTRAP_ROOT}/core-sdk/generated/typescript"
JSON_OUT_DIR="${BOOTSTRAP_ROOT}/core-sdk/generated/jsonschema"

if [[ ! -d "${PROTO_SRC}" ]]; then
  echo "[core-dna] Pasta de protos nao encontrada: ${PROTO_SRC}" >&2
  exit 1
fi

mkdir -p "${PY_OUT_DIR}" "${TS_OUT_DIR}" "${JSON_OUT_DIR}"
touch "${PY_OUT_DIR}/__init__.py"

resolve_proto() {
  local filename="$1"

  if [[ -f "${PROTO_SRC}/${filename}" ]]; then
    printf '%s\n' "${PROTO_SRC}/${filename}"
    return 0
  fi

  if [[ -f "${LEGACY_PROTO_SRC}/${filename}" ]]; then
    printf '%s\n' "${LEGACY_PROTO_SRC}/${filename}"
    return 0
  fi

  return 1
}

PROTO_FILES=(
  "$(resolve_proto events.proto)"
  "$(resolve_proto event_envelope.proto)"
  "$(resolve_proto property.proto)"
  "$(resolve_proto user.proto)"
)

PROTO_INCLUDE_ARGS=("-I" "${PROTO_SRC}")

if [[ -d "${LEGACY_PROTO_SRC}" && "${LEGACY_PROTO_SRC}" != "${PROTO_SRC}" ]]; then
  PROTO_INCLUDE_ARGS+=("-I" "${LEGACY_PROTO_SRC}")
fi

for proto in "${PROTO_FILES[@]}"; do
  if [[ ! -f "${proto}" ]]; then
    echo "[core-dna] Proto obrigatorio ausente: ${proto}" >&2
    exit 1
  fi
done

# Validação de eventos antes de build
echo "[core-dna] Validando eventos registrados..."
python3 "$REPO_ROOT/scripts/check_events.py"

echo "[core-dna] Compilando protos para ${PY_OUT_DIR}"

if command -v protoc >/dev/null 2>&1; then
  protoc \
    "${PROTO_INCLUDE_ARGS[@]}" \
    --python_out "${PY_OUT_DIR}" \
    "${PROTO_FILES[@]}"
else
  if ! python3 -m grpc_tools.protoc --version >/dev/null 2>&1; then
    echo "[core-dna] grpc_tools nao encontrado. Instalando grpcio-tools..."
    python3 -m pip install --user --quiet grpcio-tools
  fi

  python3 -m grpc_tools.protoc \
    "${PROTO_INCLUDE_ARGS[@]}" \
    --python_out "${PY_OUT_DIR}" \
    "${PROTO_FILES[@]}"
fi

python3 "${SCRIPT_DIR}/generate_dna_artifacts.py" \
  --proto "${PROTO_SRC}/events.proto" \
  --ts-out "${TS_OUT_DIR}/events.ts" \
  --json-out "${JSON_OUT_DIR}/events.schema.json"

echo "[core-dna] Build concluido com sucesso."
