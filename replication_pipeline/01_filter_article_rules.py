from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from replication_common import (
    METADATA_COLUMNS,
    coincidence_statistics,
    flatten_records,
    is_missing,
    load_records,
    save_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aplica as regras de seleção de atributos descritas no artigo."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/input/anonymous_fingerprints.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/intermediate/filtering"),
    )
    parser.add_argument(
        "--max-duration-ms",
        type=float,
        default=100.0,
        help="Tmax da Equação (1). O artigo usa 100 ms no experimento.",
    )
    parser.add_argument(
        "--p-max",
        type=float,
        default=0.5,
        help="Pmax da Equação (4). O artigo usa 0,5 no experimento.",
    )
    parser.add_argument(
        "--uniqueness-source",
        choices=["value", "duration", "either"],
        default="value",
        help=(
            "Sinal usado na Equação (5). 'value' segue a tabela final do artigo; "
            "'duration' usa tempos; 'either' aprova quando valor ou tempo passa."
        ),
    )
    args = parser.parse_args()

    if args.max_duration_ms <= 0:
        raise ValueError("--max-duration-ms deve ser positivo.")
    if not 0 <= args.p_max <= 1:
        raise ValueError("--p-max deve estar entre 0 e 1.")
    if not args.input.exists():
        raise FileNotFoundError(args.input)

    records = load_records(args.input)
    values, durations = flatten_records(records)
    features = [column for column in values.columns if column not in METADATA_COLUMNS]
    n = len(values)
    rows: list[dict] = []

    for feature in features:
        value_series = values[feature]
        duration_series = pd.to_numeric(durations[feature], errors="coerce")

        unique_values, max_value_frequency, value_probability = (
            coincidence_statistics(value_series)
        )
        unique_durations, max_duration_frequency, duration_probability = (
            coincidence_statistics(duration_series)
        )

        values_complete = bool((~value_series.map(is_missing)).all())
        durations_complete = bool(duration_series.notna().all())
        average_duration = (
            float(duration_series.mean()) if duration_series.notna().any() else np.nan
        )

        passes_duration = bool(
            pd.notna(average_duration) and average_duration < args.max_duration_ms
        )
        passes_completeness = values_complete and durations_complete
        passes_value_uniqueness = value_probability < args.p_max
        passes_duration_uniqueness = duration_probability < args.p_max

        if args.uniqueness_source == "value":
            passes_uniqueness = passes_value_uniqueness
            probability_used = value_probability
        elif args.uniqueness_source == "duration":
            passes_uniqueness = passes_duration_uniqueness
            probability_used = duration_probability
        else:
            passes_uniqueness = (
                passes_value_uniqueness or passes_duration_uniqueness
            )
            probability_used = min(value_probability, duration_probability)

        selected = passes_duration and passes_completeness and passes_uniqueness

        reasons: list[str] = []
        if not passes_duration:
            reasons.append("average_duration_not_below_tmax")
        if not passes_completeness:
            reasons.append("value_or_duration_missing")
        if not passes_uniqueness:
            reasons.append("coincidence_probability_not_below_pmax")

        rows.append(
            {
                "feature": feature,
                "records": n,
                "average_duration_ms": average_duration,
                "values_complete": values_complete,
                "durations_complete": durations_complete,
                "unique_values": unique_values,
                "max_value_frequency_m": max_value_frequency,
                "value_coincidence_probability": value_probability,
                "unique_durations": unique_durations,
                "max_duration_frequency_m": max_duration_frequency,
                "duration_coincidence_probability": duration_probability,
                "uniqueness_source": args.uniqueness_source,
                "coincidence_probability_used": probability_used,
                "passes_duration_rule": passes_duration,
                "passes_completeness_rule": passes_completeness,
                "passes_uniqueness_rule": passes_uniqueness,
                "selected": selected,
                "exclusion_reason": ";".join(reasons),
            }
        )

    stats = pd.DataFrame(rows).sort_values("feature").reset_index(drop=True)
    selected_features = stats.loc[stats["selected"], "feature"].tolist()

    if not selected_features:
        raise RuntimeError(
            "Nenhuma feature passou. Consulte feature_selection.csv e ajuste "
            "Tmax, Pmax ou --uniqueness-source."
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stats.to_csv(args.output_dir / "feature_selection.csv", index=False)
    values.to_pickle(args.output_dir / "flattened_values.pkl")
    durations.to_pickle(args.output_dir / "flattened_durations.pkl")
    save_json(
        {
            "method": "article_rule_filter",
            "equation_1": "mean_duration_j < Tmax",
            "completeness_rule": "value and duration available for every record",
            "equation_5": "P(S_j) = (m - 1) / N",
            "max_duration_ms": args.max_duration_ms,
            "p_max": args.p_max,
            "uniqueness_source": args.uniqueness_source,
            "records": n,
            "participants": int(values["participant_id"].nunique()),
            "evaluated_features": len(features),
            "selected_features": selected_features,
            "selected_count": len(selected_features),
            "implementation_note": (
                "O artigo admite que valor ou tempo pode ser identificador, mas "
                "não especifica completamente como combinar os dois sinais. "
                "A escolha foi explicitada por --uniqueness-source."
            ),
        },
        args.output_dir / "selected_features.json",
    )

    print(f"Features avaliadas: {len(features)}")
    print(f"Features selecionadas: {len(selected_features)}")
    print(", ".join(selected_features))
    print(f"Resultados: {args.output_dir}")


if __name__ == "__main__":
    main()
