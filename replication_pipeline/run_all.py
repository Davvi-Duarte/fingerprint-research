from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(*args: str) -> None:
    print("\n$", " ".join(args))
    subprocess.run(args, check=True)


def main() -> None:
    python = sys.executable
    root = Path(__file__).parent

    run(python, str(root / "00_prepare_anonymized_sample.py")) 
    run(python, str(root / "01_filter_article_rules.py"))
    run(python, str(root / "02_build_numeric_matrix.py"))
    run(python, str(root / "03_train_knn.py"))
    run(python, str(root / "04_run_article_features.py"))

    print("\nPipeline concluído.")
    print("Renderize o relatório com:")
    print("Rscript -e \"rmarkdown::render('replication_analysis.Rmd')\"")


if __name__ == "__main__":
    main()
