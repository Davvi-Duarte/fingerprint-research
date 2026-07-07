# Replicação KNN de browser fingerprints

Este projeto separa a replicação em etapas auditáveis.

## Estrutura

```text
replicacao_knn_artigo/
├── data/
│   ├── input/anonymous_fingerprints.json
│   ├── intermediate/
│   └── results/
├── replication_common.py
├── 01_filter_article_rules.py
├── 02_build_numeric_matrix.py
├── 03_train_knn.py
├── 04_run_article_features.py
├── run_all.py
├── replication_analysis.Rmd
└── requirements.txt
```

## Etapa 1 — filtragem

Aplica:

- média do tempo menor que `Tmax`;
- valor e duração presentes em todas as coletas;
- `P(Sj) = (m - 1) / N < Pmax`.

```bash
python 01_filter_article_rules.py
```

A opção `--uniqueness-source` documenta uma ambiguidade do artigo:

```bash
python 01_filter_article_rules.py --uniqueness-source value
python 01_filter_article_rules.py --uniqueness-source duration
python 01_filter_article_rules.py --uniqueness-source either
```

O padrão é `value`, porque a tabela final do artigo utiliza valores dos
atributos como entrada do KNN.

## Etapa 2 — matriz numérica

```bash
python 02_build_numeric_matrix.py
```

Valores numéricos são preservados. Textos, booleanos, listas e objetos
recebem rótulos naturais determinísticos, como descrito no artigo. O mapa
completo é salvo em `category_mappings.json`.

## Etapa 3 — KNN

```bash
python 03_train_knn.py
```

Usa:

- distância euclidiana;
- pesos uniformes;
- K de 1 a 9;
- validação leave-one-out;
- limiar de autenticidade 0,5.

## Etapa 4 — atributos finais do artigo

```bash
python 04_run_article_features.py
```

Esse cenário usa diretamente:

- domBlockers;
- audio;
- timezone;
- localStorage;
- plugins;
- largura e altura de screenResolution;
- hardwareConcurrency;
- platform.

Ele é uma comparação, não a replicação da etapa de seleção.

## Executar tudo

```bash
python run_all.py
```

## Relatório

Pacotes R:

```r
install.packages(c("rmarkdown", "tidyverse", "jsonlite", "knitr", "scales"))
```

Renderização:

```bash
Rscript -e "rmarkdown::render('replication_analysis.Rmd')"
```

## Observações

O dataset atual contém 100 coletas, 10 participantes e 10 coletas por
participante. O artigo não fornece todos os detalhes de avaliação e
pré-processamento; decisões não especificadas são registradas nos JSONs
de metadados para permitir validação e discussão.
