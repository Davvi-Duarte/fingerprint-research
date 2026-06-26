from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

TARGET_PARTICIPANTS = [
    "Luiza Oliveira De Carvalho",
    "Maria Luiza Andrade Cavalcanti",
    "Vinícius De Oliveira Porto",
    "Bruno Grangeiro Bonifácio",
    "Davvi Duarte Rodrigues",
    "José Jardel Alves De Medeiros",
    "David Joshua Galvíncio De Souza",
    "Walber Wesley Félix De Araújo Filho",
    "Júlia Oliveira Kanuto Menezes",
    "Filipe Magno Alves Paiva",
]

COLLECTIONS_PER_PARTICIPANT = 6


def normalize_name(value: str) -> str:
    """Normaliza caixa, acentos e espaços somente para localizar participantes."""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.casefold().strip()
    return re.sub(r"\s+", " ", normalized)


def stable_participant_id(index: int) -> str:
    return f"participant_{index:03d}"


def sanitize_component(component: Any) -> dict[str, Any]:
    """Mantém apenas valor e duração necessários para reproduzir o artigo."""
    if not isinstance(component, dict):
        return {"value": component, "duration": None}

    return {
        "value": component.get("value"),
        "duration": component.get("duration"),
    }


def load_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    if isinstance(payload, list):
        return payload
    raise ValueError("Formato inválido: esperado {'records': [...]} ou uma lista.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Seleciona as seis primeiras coletas de participantes definidos e "
            "gera um conjunto anonimizado para replicação."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("dados_completos.json"),
        help="JSON completo na raiz do projeto.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/replication/anonymous_fingerprints.json"),
        help="JSON anonimizado gerado.",
    )
    parser.add_argument(
        "--collections",
        type=int,
        default=COLLECTIONS_PER_PARTICIPANT,
        help="Quantidade de coletas por participante.",
    )
    args = parser.parse_args()

    if args.collections < 1:
        raise ValueError("--collections deve ser maior que zero.")
    if not args.input.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {args.input.resolve()}")

    records = load_records(args.input)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        participant_name = record.get("participant_name")
        if isinstance(participant_name, str):
            grouped[normalize_name(participant_name)].append(record)

    output_records: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []

    for participant_index, requested_name in enumerate(TARGET_PARTICIPANTS, start=1):
        normalized_target = normalize_name(requested_name)
        participant_records = grouped.get(normalized_target, [])

        if len(participant_records) < args.collections:
            raise ValueError(
                f"Participante '{requested_name}' possui {len(participant_records)} "
                f"coleta(s), mas {args.collections} são necessárias."
            )

        participant_id = stable_participant_id(participant_index)
        selected = participant_records[: args.collections]

        for collection_index, record in enumerate(selected, start=1):
            fingerprint_result = record.get("fingerprint_result", {})
            components = fingerprint_result.get("components", {})
            if not isinstance(components, dict):
                raise ValueError(
                    f"components inválido para {participant_id}, coleta {collection_index}."
                )

            output_records.append(
                {
                    "participant_id": participant_id,
                    "collection_id": f"{participant_id}_collection_{collection_index:02d}",
                    "collection_index": collection_index,
                    "components": {
                        key: sanitize_component(value)
                        for key, value in sorted(components.items())
                    },
                }
            )

        summary.append(
            {
                "participant_id": participant_id,
                "available_collections": len(participant_records),
                "selected_collections": len(selected),
            }
        )

    # Hash apenas para verificar integridade; não permite recuperar nomes.
    source_digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    output_payload = {
        "schema_version": "1.0",
        "description": (
            "Dataset anonimizado para replicação de identificação por browser fingerprint."
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

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(output_payload, file, ensure_ascii=False, indent=2)

    print(f"Dataset anonimizado criado: {args.output}")
    print(f"Participantes: {len(TARGET_PARTICIPANTS)}")
    print(f"Coletas por participante: {args.collections}")
    print(f"Total de registros: {len(output_records)}")
    print("Nomes, visitorId, confiança e versão não foram exportados.")


if __name__ == "__main__":
    main()
