from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


METADATA_COLUMNS = ["participant_id", "collection_id", "collection_index"]

# Atributos apresentados na Figura 1 do artigo.
# O artigo chama as dimensões de sR1 e sR2. Aqui usamos nomes descritivos.
ARTICLE_FEATURES = [
    "domBlockers",
    "audio",
    "timezone",
    "localStorage",
    "plugins",
    "screenResolution_width",
    "screenResolution_height",
    "hardwareConcurrency",
    "platform",
]


def load_records(path: Path) -> list[dict[str, Any]]:
    """Lê o JSON anonimizado e devolve a lista de coletas."""
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise ValueError("Esperado um JSON com {'records': [...]} ou uma lista não vazia.")
    return records


def is_missing(value: Any) -> bool:
    """Ausência de valor. Zero e False são valores válidos."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def canonical_value(value: Any) -> str:
    """
    Serializa valores complexos de maneira determinística.

    Listas e objetos inteiros são tratados como uma categoria, porque o artigo
    apenas informa que valores textuais são substituídos por rótulos naturais.
    """
    if is_missing(value):
        return "__MISSING__"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def flatten_records(
    records: list[dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Converte o JSON aninhado em duas tabelas:
    - valores das features;
    - tempos de cálculo em milissegundos.

    screenResolution=[largura, altura] é dividido em duas colunas, conforme a
    tabela final do artigo.
    """
    value_rows: list[dict[str, Any]] = []
    duration_rows: list[dict[str, Any]] = []

    for position, record in enumerate(records, start=1):
        participant_id = record.get("participant_id")
        collection_id = record.get("collection_id")
        collection_index = record.get("collection_index", position)
        components = record.get("components")

        if not participant_id or not collection_id or not isinstance(components, dict):
            raise ValueError(
                f"Registro {position} inválido: participant_id, collection_id "
                "e components são obrigatórios."
            )

        values: dict[str, Any] = {
            "participant_id": str(participant_id),
            "collection_id": str(collection_id),
            "collection_index": collection_index,
        }
        durations: dict[str, Any] = dict(values)

        for name, component in components.items():
            if isinstance(component, dict):
                value = component.get("value")
                duration = component.get("duration")
            else:
                value = component
                duration = None

            if name == "screenResolution":
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    values["screenResolution_width"] = value[0]
                    values["screenResolution_height"] = value[1]
                else:
                    values["screenResolution_width"] = None
                    values["screenResolution_height"] = None
                durations["screenResolution_width"] = duration
                durations["screenResolution_height"] = duration
            else:
                values[name] = value
                durations[name] = duration

        value_rows.append(values)
        duration_rows.append(durations)

    values_df = pd.DataFrame(value_rows)
    durations_df = pd.DataFrame(duration_rows)

    # Garante as mesmas colunas de features nas duas tabelas.
    feature_columns = sorted(
        (set(values_df.columns) | set(durations_df.columns)) - set(METADATA_COLUMNS)
    )
    for feature in feature_columns:
        if feature not in values_df:
            values_df[feature] = None
        if feature not in durations_df:
            durations_df[feature] = np.nan

    ordered = METADATA_COLUMNS + feature_columns
    return values_df[ordered], durations_df[ordered]


def coincidence_statistics(series: pd.Series) -> tuple[int, int, float]:
    """
    Implementa a Equação (5) do artigo:
        P(S_j) = (m - 1) / N

    m é a maior quantidade de valores coincidentes para a feature e N é o
    número total de registros. Valores ausentes continuam contabilizados na
    estatística, mas a regra de completude os reprova separadamente.
    """
    canonical = series.map(canonical_value)
    counts = Counter(canonical)
    n = len(canonical)
    m = max(counts.values()) if counts else n
    probability = (m - 1) / n if n else float("nan")
    return int(canonical.nunique(dropna=False)), int(m), float(probability)


def read_feature_list(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("selected_features")
    if not isinstance(features, list) or not features:
        raise ValueError(f"Lista de features inválida em {path}")
    return [str(item) for item in features]


def save_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def build_natural_number_matrix(
    values: pd.DataFrame,
    selected_features: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Monta a matriz numérica segundo a descrição do artigo.

    - Colunas totalmente numéricas são mantidas como números.
    - Valores textuais, booleanos, listas e objetos recebem rótulos naturais
      determinísticos: 0, 1, 2, ...
    - Não há padronização/normalização, pois o artigo não descreve essa etapa.
    """
    missing = [name for name in selected_features if name not in values.columns]
    if missing:
        raise ValueError(f"Features ausentes no dataset: {missing}")

    result = values[METADATA_COLUMNS].copy()
    mappings: dict[str, Any] = {}

    for feature in selected_features:
        original = values[feature]
        converted = pd.to_numeric(original, errors="coerce")
        all_present = not original.map(is_missing).any()
        fully_numeric = all_present and converted.notna().all()

        if fully_numeric:
            result[feature] = converted.astype(float)
            mappings[feature] = {
                "kind": "numeric",
                "transformation": "identity",
            }
            continue

        canonical = original.map(canonical_value)
        categories = sorted(canonical.unique().tolist())
        category_to_code = {category: index for index, category in enumerate(categories)}
        result[feature] = canonical.map(category_to_code).astype(int)
        mappings[feature] = {
            "kind": "categorical",
            "transformation": "natural_number_label",
            "missing_token": "__MISSING__",
            "mapping": category_to_code,
        }

    return result, mappings
