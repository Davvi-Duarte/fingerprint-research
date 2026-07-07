from __future__ import annotations

import argparse
from pathlib import Path

from replication_common import (
    build_natural_number_matrix,
    flatten_records,
    load_records,
    read_feature_list,
    save_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transforma as features selecionadas em uma matriz numérica."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/input/anonymous_fingerprints.json"),
    )
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/intermediate/filtering/selected_features.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/intermediate/matrix_filtered"),
    )
    args = parser.parse_args()

    records = load_records(args.input)
    values, _ = flatten_records(records)
    selected = read_feature_list(args.features)
    matrix, mappings = build_natural_number_matrix(values, selected)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(args.output_dir / "numeric_matrix.csv", index=False)
    save_json(mappings, args.output_dir / "category_mappings.json")
    save_json(
        {
            "records": len(matrix),
            "participants": int(matrix["participant_id"].nunique()),
            "features": selected,
            "feature_count": len(selected),
            "categorical_encoding": "deterministic natural-number labels",
            "numeric_transformation": "identity",
            "scaling": "none",
            "reason_for_no_scaling": (
                "O artigo descreve a substituição de valores textuais por "
                "rótulos naturais, mas não descreve normalização de escala."
            ),
        },
        args.output_dir / "matrix_metadata.json",
    )

    print(f"Matriz: {matrix.shape[0]} linhas x {len(selected)} features")
    print(f"Arquivo: {args.output_dir / 'numeric_matrix.csv'}")


if __name__ == "__main__":
    main()
