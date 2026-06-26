# Pipeline de replicação anonimizada

## Estrutura

- `01_prepare_anonymized_dataset.py`: seleciona seis coletas de cada participante e remove identificadores pessoais.
- `02_run_article_replication.py`: seleciona atributos, codifica os valores e executa KNN com validação leave-one-out.
- `replication_report.Rmd`: gera gráficos e tabelas para comparação com o artigo.

## Execução

Coloque `dados_completos.json` na raiz do projeto e execute:

```bash
python 01_prepare_anonymized_dataset.py
python 02_run_article_replication.py --feature-mode article
```

Para aplicar automaticamente os critérios de seleção descritos no artigo:

```bash
python 02_run_article_replication.py --feature-mode automatic
```

Depois, no R:

```r
install.packages(c("rmarkdown", "tidyverse", "knitr", "scales"))
rmarkdown::render("replication_report.Rmd")
```

## Open Science

O JSON público contém apenas IDs anônimos, índices de coleta, valores e durações dos componentes. Nomes, `visitorId`, confiança e versão do SDK não são exportados. O arquivo bruto e qualquer tabela que relacione nomes a IDs anônimos não devem ser publicados.
