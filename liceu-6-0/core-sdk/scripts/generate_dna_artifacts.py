from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_events(proto_path: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    in_enum = False
    pending_key: str | None = None
    pending_versions: list[str] = []

    for raw_line in proto_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line.startswith("enum CanonicalEventType"):
            in_enum = True
            continue

        if in_enum and line == "}":
            break

        if not in_enum:
            continue

        key_match = re.match(r"//\s*key:\s*(.+)$", line)
        if key_match:
            pending_key = key_match.group(1).strip()
            continue

        versions_match = re.match(r"//\s*versions:\s*(.+)$", line)
        if versions_match:
            pending_versions = [item.strip() for item in versions_match.group(1).split(",") if item.strip()]
            continue

        enum_match = re.match(r"([A-Z0-9_]+)\s*=\s*\d+;", line)
        if not enum_match:
            continue

        enum_name = enum_match.group(1)
        if enum_name == "CANONICAL_EVENT_TYPE_UNSPECIFIED":
            pending_key = None
            pending_versions = []
            continue

        event_key = pending_key or enum_name.lower().replace("_", ".")
        versions = pending_versions or ["v1"]
        entries.append(
            {
                "enum_name": enum_name,
                "event_key": event_key,
                "versions": versions,
            }
        )
        pending_key = None
        pending_versions = []

    if not entries:
        raise ValueError(f"Nenhum evento canonico encontrado em {proto_path}")

    return entries


def build_typescript(events: list[dict[str, object]]) -> str:
    version_values = sorted({version for event in events for version in event["versions"]})
    lines = [
        "export const EVENT_VERSIONS = [",
    ]
    for version in version_values:
        lines.append(f'  "{version}",')
    lines.extend(
        [
            "] as const;",
            "",
            "export type EventVersion = (typeof EVENT_VERSIONS)[number];",
            "",
            "export const CANONICAL_EVENTS = {",
        ]
    )
    for event in events:
        lines.append(f'  {event["enum_name"]}: "{event["event_key"]}",')
    lines.extend(
        [
            "} as const;",
            "",
            "export type CanonicalEventType = (typeof CANONICAL_EVENTS)[keyof typeof CANONICAL_EVENTS];",
            "",
            "export interface EventEnvelope {",
            "  id: string;",
            "  type: CanonicalEventType;",
            "  version: EventVersion;",
            "  source: string;",
            "  timestamp: string;",
            "  payload: Record<string, string>;",
            "}",
            "",
            "export const EVENT_CATALOG = [",
        ]
    )
    for event in events:
        versions = ", ".join(f'"{version}"' for version in event["versions"])
        lines.append("  {")
        lines.append(f'    enumName: "{event["enum_name"]}",')
        lines.append(f'    eventKey: "{event["event_key"]}",')
        lines.append(f"    versions: [{versions}] as const,")
        lines.append("  },")
    lines.extend(["] as const;", ""])
    return "\n".join(lines)


def build_json_schema(events: list[dict[str, object]]) -> dict[str, object]:
    version_values = sorted({version for event in events for version in event["versions"]})
    event_keys = [str(event["event_key"]) for event in events]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://liceu.local/schemas/events.schema.json",
        "title": "LICEU Canonical Event Envelope",
        "type": "object",
        "required": ["id", "type", "version", "source", "timestamp", "payload"],
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string", "minLength": 1},
            "type": {"type": "string", "enum": event_keys},
            "version": {"type": "string", "enum": version_values},
            "source": {"type": "string", "minLength": 1},
            "timestamp": {"type": "string", "format": "date-time"},
            "payload": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
        },
        "x-liceu-canonical-events": [
            {
                "enum_name": event["enum_name"],
                "event_key": event["event_key"],
                "versions": event["versions"],
            }
            for event in events
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera artefatos do CORE-DNA para TypeScript e JSON Schema.")
    parser.add_argument("--proto", required=True)
    parser.add_argument("--ts-out", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    proto_path = Path(args.proto)
    ts_out = Path(args.ts_out)
    json_out = Path(args.json_out)

    events = parse_events(proto_path)

    ts_out.parent.mkdir(parents=True, exist_ok=True)
    ts_out.write_text(build_typescript(events), encoding="utf-8")

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(build_json_schema(events), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()