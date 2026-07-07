from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


METADATA_COLUMNS = ["participant_id", "collection_id", "collection_index"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Avalia KNN em configuração one-vs-rest para replicação metodológica."
    )
    parser.add_argument(
        "--matrix",
        default="data/intermediate/matrix_filtered/numeric_matrix.csv",
        help="Caminho para a matriz numérica.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/results/filtered_one_vs_rest",
        help="Diretório de saída dos resultados.",
    )
    parser.add_argument(
        "--max-neighbors",
        type=int,
        default=9,
        help="Maior valor de K avaliado.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Limiar de autenticação.",
    )
    return parser.parse_args()


def leave_one_out_one_vs_rest(
    df: pd.DataFrame,
    features: list[str],
    target_participant: str,
    k: int,
    threshold: float,
) -> list[dict]:
    rows = []

    X = df[features].to_numpy(dtype=float)
    y = (df["participant_id"] == target_participant).astype(int).to_numpy()

    for test_idx in range(len(df)):
        train_idx = np.arange(len(df)) != test_idx

        X_train = X[train_idx]
        y_train = y[train_idx]
        X_test = X[test_idx].reshape(1, -1)
        y_true = int(y[test_idx])

        model = KNeighborsClassifier(
            n_neighbors=k,
            metric="euclidean",
            weights="uniform",
        )
        model.fit(X_train, y_train)

        neighbors = model.kneighbors(X_test, return_distance=False)[0]
        neighbor_labels = y_train[neighbors]

        authenticity_probability = float(np.mean(neighbor_labels))
        y_pred = int(authenticity_probability > threshold)

        rows.append(
            {
                "target_participant": target_participant,
                "collection_id": df.iloc[test_idx]["collection_id"],
                "true_participant": df.iloc[test_idx]["participant_id"],
                "k": k,
                "y_true": y_true,
                "y_pred": y_pred,
                "authenticity_probability": authenticity_probability,
                "authenticated": y_pred == 1,
                "correct": y_true == y_pred,
            }
        )

    return rows


def summarize_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    summary_rows = []

    for (target_participant, k), group in predictions.groupby(["target_participant", "k"]):
        y_true = group["y_true"].to_numpy()
        y_pred = group["y_pred"].to_numpy()

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

        summary_rows.append(
            {
                "target_participant": target_participant,
                "k": k,
                "accuracy": accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1": f1_score(y_true, y_pred, zero_division=0),
                "true_positive": int(tp),
                "false_positive": int(fp),
                "true_negative": int(tn),
                "false_negative": int(fn),
                "false_acceptance_rate": fp / (fp + tn) if (fp + tn) else 0.0,
                "false_rejection_rate": fn / (fn + tp) if (fn + tp) else 0.0,
                "mean_authenticity_probability": group["authenticity_probability"].mean(),
            }
        )

    return pd.DataFrame(summary_rows)


def main() -> None:
    args = parse_args()

    matrix_path = Path(args.matrix)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(matrix_path)

    features = [col for col in df.columns if col not in METADATA_COLUMNS]
    participants = sorted(df["participant_id"].unique())

    all_predictions = []

    max_k = min(args.max_neighbors, len(df) - 1)

    for participant in participants:
        for k in range(1, max_k + 1):
            predictions = leave_one_out_one_vs_rest(
                df=df,
                features=features,
                target_participant=participant,
                k=k,
                threshold=args.threshold,
            )
            all_predictions.extend(predictions)

    predictions_df = pd.DataFrame(all_predictions)
    summary_by_participant = summarize_predictions(predictions_df)

    summary_by_k = (
        summary_by_participant
        .groupby("k", as_index=False)
        .agg(
            mean_accuracy=("accuracy", "mean"),
            mean_precision=("precision", "mean"),
            mean_recall=("recall", "mean"),
            mean_f1=("f1", "mean"),
            mean_false_acceptance_rate=("false_acceptance_rate", "mean"),
            mean_false_rejection_rate=("false_rejection_rate", "mean"),
            mean_authenticity_probability=("mean_authenticity_probability", "mean"),
        )
    )

    best_row = summary_by_k.sort_values(
        ["mean_accuracy", "mean_f1"],
        ascending=False,
    ).iloc[0]

    metadata = {
        "evaluation": "one-vs-rest",
        "matrix": str(matrix_path),
        "output_dir": str(output_dir),
        "features": features,
        "participants": participants,
        "threshold": args.threshold,
        "max_neighbors": max_k,
        "best_k": int(best_row["k"]),
        "best_mean_accuracy": float(best_row["mean_accuracy"]),
        "best_mean_f1": float(best_row["mean_f1"]),
    }

    predictions_df.to_csv(output_dir / "one_vs_rest_predictions.csv", index=False)
    summary_by_participant.to_csv(output_dir / "one_vs_rest_summary_by_participant.csv", index=False)
    summary_by_k.to_csv(output_dir / "one_vs_rest_summary_by_k.csv", index=False)

    with open(output_dir / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("Avaliação one-vs-rest concluída.")
    print(f"Melhor K: {metadata['best_k']}")
    print(f"Acurácia média: {metadata['best_mean_accuracy']:.4f}")
    print(f"F1 médio: {metadata['best_mean_f1']:.4f}")
    print(f"Resultados salvos em: {output_dir}")


if __name__ == "__main__":
    main()