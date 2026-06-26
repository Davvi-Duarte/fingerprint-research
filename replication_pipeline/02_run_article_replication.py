from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

# Conjunto final exibido na Figura 1 do artigo.
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

ARTICLE_BASE_COMPONENTS = {
    "domBlockers",
    "audio",
    "timezone",
    "localStorage",
    "plugins",
    "screenResolution",
    "hardwareConcurrency",
    "platform",
}


def canonical_value(value: Any) -> str:
    """Transforma valores complexos em texto estável para codificação categórica."""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if value is None:
        return "__MISSING__"
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def load_dataset(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    records = payload.get("records") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not records:
        raise ValueError("Dataset vazio ou em formato inválido.")
    return records


def flatten_records(records: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    value_rows: list[dict[str, Any]] = []
    duration_rows: list[dict[str, Any]] = []

    for record in records:
        participant_id = record.get("participant_id")
        collection_id = record.get("collection_id")
        components = record.get("components", {})
        if not participant_id or not collection_id or not isinstance(components, dict):
            raise ValueError("Registro sem participant_id, collection_id ou components válidos.")

        values: dict[str, Any] = {
            "participant_id": participant_id,
            "collection_id": collection_id,
        }
        durations: dict[str, Any] = {
            "participant_id": participant_id,
            "collection_id": collection_id,
        }

        for name, component in components.items():
            component = component if isinstance(component, dict) else {"value": component}
            value = component.get("value")
            duration = component.get("duration")

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

    return pd.DataFrame(value_rows), pd.DataFrame(duration_rows)


def feature_statistics(values: pd.DataFrame, durations: pd.DataFrame) -> pd.DataFrame:
    metadata = {"participant_id", "collection_id"}
    feature_names = sorted(set(values.columns) - metadata)
    rows: list[dict[str, Any]] = []
    total = len(values)

    for feature in feature_names:
        series = values[feature] if feature in values else pd.Series([None] * total)
        duration = (
            pd.to_numeric(durations[feature], errors="coerce")
            if feature in durations
            else pd.Series([np.nan] * total)
        )
        canonical = series.map(canonical_value)
        counts = Counter(canonical)
        max_frequency = max(counts.values()) if counts else total

        # Equação (5) interpretada pela maior frequência de coincidência.
        coincidence_probability = (max_frequency - 1) / total
        complete = bool((~series.map(is_missing)).all())
        average_duration = float(duration.mean()) if duration.notna().any() else np.nan

        rows.append(
            {
                "feature": feature,
                "average_duration_ms": average_duration,
                "complete_for_all_records": complete,
                "unique_values": int(canonical.nunique(dropna=False)),
                "max_value_frequency": int(max_frequency),
                "coincidence_probability": coincidence_probability,
            }
        )

    return pd.DataFrame(rows)


def choose_features(
    stats: pd.DataFrame,
    mode: str,
    max_duration_ms: float,
    p_max: float,
) -> tuple[list[str], pd.DataFrame]:
    stats = stats.copy()
    stats["passes_duration"] = (
        stats["average_duration_ms"].isna()
        | (stats["average_duration_ms"] < max_duration_ms)
    )
    stats["passes_completeness"] = stats["complete_for_all_records"]
    stats["passes_uniqueness"] = stats["coincidence_probability"] < p_max
    stats["selected_automatically"] = (
        stats["passes_duration"]
        & stats["passes_completeness"]
        & stats["passes_uniqueness"]
    )
    stats["listed_in_article_figure"] = stats["feature"].isin(ARTICLE_FEATURES)

    if mode == "article":
        available = set(stats["feature"])
        missing = [feature for feature in ARTICLE_FEATURES if feature not in available]
        if missing:
            raise ValueError(f"Features do artigo ausentes no dataset: {missing}")
        selected = ARTICLE_FEATURES.copy()
    else:
        selected = stats.loc[stats["selected_automatically"], "feature"].tolist()

    stats["selected_for_model"] = stats["feature"].isin(selected)
    if not selected:
        raise ValueError("Nenhuma feature foi selecionada.")
    return selected, stats


def infer_feature_types(frame: pd.DataFrame, selected: list[str]) -> tuple[list[str], list[str]]:
    numeric: list[str] = []
    categorical: list[str] = []

    for feature in selected:
        converted = pd.to_numeric(frame[feature], errors="coerce")
        if converted.notna().all():
            numeric.append(feature)
        else:
            categorical.append(feature)
    return numeric, categorical


def build_model(numeric: list[str], categorical: list[str], k: int) -> Pipeline:
    transformers = []
    if numeric:
        transformers.append(("numeric", "passthrough", numeric))
    if categorical:
        transformers.append(
            (
                "categorical",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
                categorical,
            )
        )

    preprocess = ColumnTransformer(transformers=transformers, remainder="drop")
    return Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("knn", KNeighborsClassifier(n_neighbors=k, metric="euclidean")),
        ]
    )


def leave_one_out_evaluation(
    frame: pd.DataFrame,
    selected: list[str],
    max_neighbors: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    numeric, categorical = infer_feature_types(frame, selected)
    X = frame[selected].copy()
    # OrdinalEncoder exige categorias hashable e de tipo uniforme.
    # Listas/dicionários são serializados de forma canônica.
    for feature in categorical:
        X[feature] = X[feature].map(canonical_value)
    for feature in numeric:
        X[feature] = pd.to_numeric(X[feature], errors="raise")

    y = frame["participant_id"].astype(str).to_numpy()
    collection_ids = frame["collection_id"].astype(str).to_numpy()
    n = len(frame)
    max_k = min(max_neighbors, n - 1)

    detail_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    predictions_by_k: dict[int, list[str]] = {}

    for k in range(1, max_k + 1):
        predictions: list[str] = []
        authenticity_probabilities: list[float] = []

        for test_index in range(n):
            train_mask = np.arange(n) != test_index
            X_train = X.loc[train_mask]
            X_test = X.iloc[[test_index]]
            y_train = y[train_mask]

            model = build_model(numeric, categorical, k)
            model.fit(X_train, y_train)
            prediction = str(model.predict(X_test)[0])
            predictions.append(prediction)

            transformed_train = model.named_steps["preprocess"].transform(X_train)
            transformed_test = model.named_steps["preprocess"].transform(X_test)
            neighbor_positions = model.named_steps["knn"].kneighbors(
                transformed_test,
                n_neighbors=k,
                return_distance=False,
            )[0]
            neighbor_labels = y_train[neighbor_positions]
            authenticity_probability = float(np.mean(neighbor_labels == y[test_index]))
            authenticity_probabilities.append(authenticity_probability)

            detail_rows.append(
                {
                    "k": k,
                    "collection_id": collection_ids[test_index],
                    "true_participant": y[test_index],
                    "predicted_participant": prediction,
                    "correct": prediction == y[test_index],
                    "authenticity_probability": authenticity_probability,
                    "authenticated_at_0_5": authenticity_probability >= 0.5,
                }
            )

        predictions_by_k[k] = predictions
        summary_rows.append(
            {
                "k": k,
                "accuracy": accuracy_score(y, predictions),
                "mean_authenticity_probability": float(
                    np.mean(authenticity_probabilities)
                ),
                "authentication_rate_at_0_5": float(
                    np.mean(np.asarray(authenticity_probabilities) >= 0.5)
                ),
            }
        )

    chosen_predictions = predictions_by_k[1]
    labels = sorted(set(y))
    confusion = confusion_matrix(y, chosen_predictions, labels=labels)
    confusion_df = pd.DataFrame(confusion, index=labels, columns=labels)
    confusion_long = (
        confusion_df.rename_axis("true_participant")
        .reset_index()
        .melt(
            id_vars="true_participant",
            var_name="predicted_participant",
            value_name="count",
        )
    )

    return (
        pd.DataFrame(summary_rows),
        pd.DataFrame(detail_rows),
        confusion_long,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replica seleção de features e KNN do artigo de browser fingerprint."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/replication/anonymous_fingerprints.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/replication/results"),
    )
    parser.add_argument(
        "--feature-mode",
        choices=["article", "automatic"],
        default="article",
        help=(
            "article usa as nove features da Figura 1; automatic aplica os "
            "critérios de tempo, completude e coincidência."
        ),
    )
    parser.add_argument("--max-duration-ms", type=float, default=100.0)
    parser.add_argument("--p-max", type=float, default=0.5)
    parser.add_argument("--max-neighbors", type=int, default=9)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {args.input.resolve()}")

    records = load_dataset(args.input)
    values, durations = flatten_records(records)
    stats = feature_statistics(values, durations)
    selected, stats = choose_features(
        stats,
        mode=args.feature_mode,
        max_duration_ms=args.max_duration_ms,
        p_max=args.p_max,
    )

    summary, details, confusion = leave_one_out_evaluation(
        values,
        selected,
        max_neighbors=args.max_neighbors,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stats.to_csv(args.output_dir / "feature_selection.csv", index=False)
    summary.to_csv(args.output_dir / "knn_summary_by_k.csv", index=False)
    details.to_csv(args.output_dir / "knn_predictions.csv", index=False)
    confusion.to_csv(args.output_dir / "confusion_matrix_k1.csv", index=False)

    selected_frame = values[["participant_id", "collection_id", *selected]].copy()
    for column in selected:
        selected_frame[column] = selected_frame[column].map(canonical_value)
    selected_frame.to_csv(args.output_dir / "selected_feature_values.csv", index=False)

    run_metadata = {
        "input": str(args.input),
        "records": len(values),
        "participants": int(values["participant_id"].nunique()),
        "collections_per_participant": values.groupby("participant_id").size().to_dict(),
        "feature_mode": args.feature_mode,
        "selected_features": selected,
        "max_duration_ms": args.max_duration_ms,
        "p_max": args.p_max,
        "max_neighbors": min(args.max_neighbors, len(values) - 1),
        "evaluation": "leave-one-out",
        "classifier": "KNeighborsClassifier",
        "metric": "euclidean",
    }
    with (args.output_dir / "run_metadata.json").open("w", encoding="utf-8") as file:
        json.dump(run_metadata, file, ensure_ascii=False, indent=2)

    print("Replicação concluída.")
    print(f"Registros: {len(values)}")
    print(f"Participantes: {values['participant_id'].nunique()}")
    print(f"Modo de features: {args.feature_mode}")
    print(f"Features selecionadas ({len(selected)}): {', '.join(selected)}")
    print(f"Resultados: {args.output_dir}")


if __name__ == "__main__":
    main()
