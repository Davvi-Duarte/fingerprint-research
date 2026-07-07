from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


# Pasta onde este script está:
# fingerprint-research/replication_pipeline/
SCRIPT_DIR = Path(__file__).resolve().parent

# Raiz do projeto:
# fingerprint-research/
PROJECT_ROOT = SCRIPT_DIR.parent

# Caminhos padrão
DEFAULT_INPUT = PROJECT_ROOT / "dados_completos.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "data" / "input" / "anonymous_fingerprints.json"


TARGET_PARTICIPANTS = [
    "NOMES A SEREM FILTRADOS"
]

COLLECTIONS_PER_PARTICIPANT = 10


def normalize_name(value: str) -> str:
    """Normaliza caixa, acentos e espaços somente para localizar participantes."""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    normalized = normalized.casefold().strip()

    return re.sub(r"\s+", " ", normalized)


def stable_participant_id(index: int) -> str:
    """Cria um identificador anônimo estável."""
    return f"participant_{index:03d}"


def sanitize_component(component: Any) -> dict[str, Any]:
    """
    Mantém apenas valor e duração necessários para reproduzir o artigo.
    """
    if not isinstance(component, dict):
        return {
            "value": component,
            "duration": None,
        }

    return {
        "value": component.get("value"),
        "duration": component.get("duration"),
    }


def load_records(path: Path) -> list[dict[str, Any]]:
    """
    Carrega os registros do JSON bruto.

    Formatos aceitos:

    {
        "records": [...]
    }

    ou:

    [...]
    """
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]

    if isinstance(payload, list):
        return payload

    raise ValueError(
        "Formato inválido: esperado {'records': [...]} ou uma lista."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Seleciona as primeiras coletas dos participantes definidos "
            "e gera um conjunto anonimizado para replicação."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=(
            "JSON completo. Por padrão, utiliza dados_completos.json "
            "na raiz do projeto."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "JSON anonimizado. Por padrão, será criado em "
            "replication_pipeline/data/input/anonymous_fingerprints.json."
        ),
    )

    parser.add_argument(
        "--collections",
        type=int,
        default=COLLECTIONS_PER_PARTICIPANT,
        help="Quantidade de coletas selecionadas por participante.",
    )

    args = parser.parse_args()

    # Garante caminhos absolutos, mesmo quando forem passados pelo terminal.
    args.input = args.input.resolve()
    args.output = args.output.resolve()

    if args.collections < 1:
        raise ValueError("--collections deve ser maior que zero.")

    if not args.input.exists():
        raise FileNotFoundError(
            f"Arquivo de entrada não encontrado: {args.input}"
        )

    records = load_records(args.input)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record_index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(
                f"O registro {record_index} não é um objeto JSON válido."
            )

        participant_name = record.get("participant_name")

        if isinstance(participant_name, str) and participant_name.strip():
            normalized_name = normalize_name(participant_name)
            grouped[normalized_name].append(record)

    output_records: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []

    for participant_index, requested_name in enumerate(
        TARGET_PARTICIPANTS,
        start=1,
    ):
        normalized_target = normalize_name(requested_name)
        participant_records = grouped.get(normalized_target, [])

        if len(participant_records) < args.collections:
            raise ValueError(
                f"Participante '{requested_name}' possui "
                f"{len(participant_records)} coleta(s), mas "
                f"{args.collections} são necessárias."
            )

        participant_id = stable_participant_id(participant_index)

        # Seleciona as primeiras coletas na ordem original do JSON.
        selected_records = participant_records[: args.collections]

        for collection_index, record in enumerate(
            selected_records,
            start=1,
        ):
            fingerprint_result = record.get("fingerprint_result")

            if not isinstance(fingerprint_result, dict):
                raise ValueError(
                    f"fingerprint_result inválido para {participant_id}, "
                    f"coleta {collection_index}."
                )

            components = fingerprint_result.get("components")

            if not isinstance(components, dict):
                raise ValueError(
                    f"components inválido para {participant_id}, "
                    f"coleta {collection_index}."
                )

            sanitized_components = {
                component_name: sanitize_component(component_value)
                for component_name, component_value
                in sorted(components.items())
            }

            output_records.append(
                {
                    "participant_id": participant_id,
                    "collection_id": (
                        f"{participant_id}_collection_"
                        f"{collection_index:02d}"
                    ),
                    "collection_index": collection_index,
                    "components": sanitized_components,
                }
            )

        summary.append(
            {
                "participant_id": participant_id,
                "available_collections": len(participant_records),
                "selected_collections": len(selected_records),
            }
        )

    # Hash utilizado apenas para verificar a integridade do arquivo de origem.
    source_digest = hashlib.sha256(
        args.input.read_bytes()
    ).hexdigest()

    output_payload = {
        "schema_version": "1.0",
        "description": (
            "Dataset anonimizado para replicação de identificação "
            "por browser fingerprint."
        ),
        "source_sha256": source_digest,
        "selection": {
            "participants": len(TARGET_PARTICIPANTS),
            "collections_per_participant": args.collections,
            "ordering_rule": "first records in source order",
        },
        "participants_summary": summary,
        "records": output_records,
        "total": len(output_records),
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with args.output.open("w", encoding="utf-8") as file:
        json.dump(
            output_payload,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Dataset anonimizado criado com sucesso.")
    print(f"Entrada: {args.input}")
    print(f"Saída: {args.output}")
    print(f"Participantes: {len(TARGET_PARTICIPANTS)}")
    print(f"Coletas por participante: {args.collections}")
    print(f"Total de registros: {len(output_records)}")
    print(
        "Nomes, visitorId, confidence e version "
        "não foram exportados."
    )


if __name__ == "__main__":
    main()