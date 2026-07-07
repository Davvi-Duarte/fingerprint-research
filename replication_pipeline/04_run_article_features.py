from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from replication_common import (
    ARTICLE_FEATURES,
    build_natural_number_matrix,
    flatten_records,
    load_records,
    save_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa o cenário one-vs-rest com os atributos finais do artigo original."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/input/anonymous_fingerprints.json"),
    )
    parser.add_argument(
        "--matrix-dir",
        type=Path,
        default=Path("data/intermediate/matrix_article"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/results/article_one_vs_rest"),
    )
    parser.add_argument("--max-neighbors", type=int, default=9)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()

    records = load_records(args.input)
    values, _ = flatten_records(records)

    matrix, mappings = build_natural_number_matrix(values, ARTICLE_FEATURES)

    args.matrix_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = args.matrix_dir / "numeric_matrix.csv"

    matrix.to_csv(matrix_path, index=False)
    save_json(mappings, args.matrix_dir / "category_mappings.json")
    save_json(
        {
            "scenario": "article_final_features_one_vs_rest",
            "features": ARTICLE_FEATURES,
            "feature_count": len(ARTICLE_FEATURES),
            "purpose": (
                "Comparar a seleção obtida nos dados atuais com o cenário em "
                "que são utilizados diretamente os atributos finais do artigo original."
            ),
            "evaluation": "one-vs-rest",
            "threshold": args.threshold,
            "warning": (
                "Este cenário não reaplica a seleção do artigo aos dados atuais; "
                "ele apenas avalia, na nova base, o conjunto de atributos finais "
                "descrito no estudo original."
            ),
        },
        args.matrix_dir / "matrix_metadata.json",
    )

    command = [
        sys.executable,
        str(Path(__file__).with_name("03_train_knn.py")),
        "--matrix",
        str(matrix_path),
        "--output-dir",
        str(args.output_dir),
        "--max-neighbors",
        str(args.max_neighbors),
        "--threshold",
        str(args.threshold),
    ]

    subprocess.run(command, check=True)

    print("Cenário one-vs-rest com atributos do artigo concluído.")
    print(f"Matriz salva em: {matrix_path}")
    print(f"Resultados salvos em: {args.output_dir}")


if __name__ == "__main__":
    main()