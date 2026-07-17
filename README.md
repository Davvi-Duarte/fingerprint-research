# Browser Fingerprinting Research

Replicação metodológica adaptada do artigo:

> **"Web user identification based on browser fingerprints using machine learning methods"**  
> Salomatin, Iskhakov & Iskhakova

Aplicação web para coleta consentida de browser fingerprints em ambiente acadêmico controlado.  
Os dados coletados são usados para reprodução parcial do experimento com algoritmo KNN.

---

## Índice

1. [Estrutura do projeto](#estrutura-do-projeto)
2. [Pré-requisitos](#pré-requisitos)
3. [Rodar localmente com Docker Compose](#rodar-localmente-com-docker-compose)
4. [Rodar localmente sem Docker](#rodar-localmente-sem-docker)
5. [Variáveis de ambiente](#variáveis-de-ambiente)
6. [Migrations do banco de dados](#migrations-do-banco-de-dados)
7. [Testar uma coleta](#testar-uma-coleta)
8. [Rotas da API](#rotas-da-api)
9. [Exportar dados para pré-processamento e KNN](#exportar-dados-para-pré-processamento-e-knn)
10. [Pipeline de replicação](#pipeline-de-replicação)
11. [Relatório estatístico (R)](#relatório-estatístico-r)
12. [Deploy em produção](#deploy-em-produção)
13. [Cuidados éticos incorporados](#cuidados-éticos-incorporados)

---

## Estrutura do projeto

```
fingerprint-research/
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Factory da aplicação Flask
│   │   ├── config.py         # Configurações por ambiente
│   │   ├── database.py       # Instância do SQLAlchemy
│   │   ├── models.py         # Modelo FingerprintRecord
│   │   ├── routes.py         # Todas as rotas da API
│   │   └── schemas.py        # Validação com Marshmallow
│   ├── migrations/           # Gerado pelo Flask-Migrate
│   ├── run.py                # Entrypoint
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConsentPage.tsx
│   │   │   └── FingerprintStatus.tsx
│   │   ├── services/
│   │   │   └── apiService.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   └── .env.example
├── replication_pipeline/         # Pipeline de replicação
│   ├── 00_prepare_anonymized_sample.py
│   ├── 01_filter_article_rules.py
│   ├── 02_build_numeric_matrix.py
│   ├── 03_train_knn.py
│   ├── 04_run_article_features.py
│   ├── replication_common.py     # Funções compartilhadas
│   ├── run_all.py                # Executa todas as etapas
│   ├── replication_analysis_one_vs_rest.Rmd
│   ├── requirements.txt
│   ├── data/
│   │   ├── input/                # Dataset anonimizado
│   │   ├── intermediate/         # Artefatos intermediários
│   │   └── results/              # Resultados finais
│   └── figures/                  # Gráficos (PNG, 300 dpi)
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
|---|---|
| Docker + Docker Compose | 24+ / 2.20+ |
| Node.js (sem Docker) | 20+ |
| Python (sem Docker) | 3.11+ |
| R (para relatório) | 4.3+ |
| PostgreSQL (opcional) | 15+ |

---

## Rodar localmente com Docker Compose

### 1. Clone e configure

```bash
git clone <url-do-repositorio>
cd fingerprint-research

# Copie e edite as variáveis de ambiente
cp .env.example .env
# Edite .env com seus valores (especialmente SECRET_KEY e POSTGRES_PASSWORD)
```

### 2. Suba os serviços

```bash
docker compose up --build
```

Aguarde as mensagens de health do PostgreSQL e o Flask realizar as migrations automaticamente.

### 3. Acesse

- **Frontend:** http://localhost:3000
- **Backend/API:** http://localhost:5000
- **Health check:** http://localhost:5000/health

### Parar os serviços

```bash
docker compose down
# Para apagar também os dados do banco:
docker compose down -v
```

---

## Rodar localmente sem Docker

### Backend

```bash
cd backend

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env — para SQLite local, mantenha DATABASE_URL=sqlite:///fingerprints.db

# Inicialize as migrations (primeira vez apenas)
export FLASK_APP=run.py
flask db init
flask db migrate -m "initial migration"
flask db upgrade

# Para migrations subsequentes após mudanças no modelo:
flask db migrate -m "describe change"
flask db upgrade

# Inicie o servidor de desenvolvimento
flask run
# O backend estará em http://localhost:5000
```

### Frontend

```bash
cd frontend

# Instale as dependências
npm install

# Configure as variáveis de ambiente
cp .env.example .env
# Certifique-se que VITE_API_URL=http://localhost:5000

# Inicie o servidor de desenvolvimento
npm run dev
# O frontend estará em http://localhost:5173
```

---

## Variáveis de ambiente

### Backend (`backend/.env`)

| Variável | Descrição | Padrão |
|---|---|---|
| `FLASK_ENV` | `development` ou `production` | `production` |
| `SECRET_KEY` | Chave secreta Flask | — **mude em produção** |
| `DATABASE_URL` | URL do banco de dados | `sqlite:///fingerprints.db` |
| `CORS_ORIGINS` | Origens permitidas (vírgula) | `*` |
| `ALLOW_RAW_EXPORT` | Habilita exportação de dados brutos | `false` |

### Frontend (`frontend/.env`)

| Variável | Descrição | Padrão |
|---|---|---|
| `VITE_API_URL` | URL base da API do backend | `http://localhost:5000` |

---

## Migrations do banco de dados

```bash
cd backend
export FLASK_APP=run.py

# Criar repositório de migrations (apenas na primeira vez)
flask db init

# Gerar migration após mudanças no models.py
flask db migrate -m "descreva a mudança"

# Aplicar migrations pendentes
flask db upgrade

# Reverter última migration
flask db downgrade
```

---

## Testar uma coleta

### Via navegador

1. Acesse http://localhost:3000
2. Leia as informações do experimento
3. Digite seu nome
4. Marque o checkbox de consentimento
5. Clique em **"Gerar e enviar fingerprint"**
6. Aguarde a confirmação

### Via cURL (teste direto na API)

```bash
curl -X POST http://localhost:5000/api/fingerprints \
  -H "Content-Type: application/json" \
  -d '{
    "participant_name": "Participante Teste",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z",
    "user_agent": "Mozilla/5.0 Test",
    "library_name": "FingerprintJS OSS",
    "visitor_id": "abc123",
    "confidence": {"score": 1.0},
    "components": {"platform": {"value": "Linux", "duration": 1}},
    "raw_result": {"visitorId": "abc123"},
    "duration_total_ms": 250.5,
    "client_started_at": "2024-01-15T10:30:00Z",
    "client_finished_at": "2024-01-15T10:30:00.250Z"
  }'
```

### Listar coletas

```bash
curl http://localhost:5000/api/fingerprints
```

---

## Rotas da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Status do backend |
| `POST` | `/api/fingerprints` | Registrar uma nova coleta |
| `GET` | `/api/fingerprints` | Listar resumos (sem dados brutos) |
| `GET` | `/api/fingerprints/<id>` | Obter resumo de um registro |
| `GET` | `/api/fingerprints/<id>/raw` | Dados brutos (requer `ALLOW_RAW_EXPORT=true`) |
| `GET` | `/api/export` | Exportar CSV ou JSON para análise |

### Parâmetros de exportação

```
GET /api/export?format=csv                   → CSV resumido (sem nomes)
GET /api/export?format=json                  → JSON resumido (sem nomes)
GET /api/export?format=csv&include_raw=true  → CSV completo (requer ALLOW_RAW_EXPORT=true)
```

### Paginação na listagem

```
GET /api/fingerprints?page=1&per_page=50
```

---

## Exportar dados para pré-processamento e KNN

### Passo 1 — Habilitar exportação bruta (apenas no ambiente de pesquisa)

No arquivo `.env` do backend:

```
ALLOW_RAW_EXPORT=true
```

Reinicie o backend.

### Passo 2 — Exportar os dados

```bash
# Exportar todos os registros resumidos como JSON
curl http://localhost:5000/api/export?format=json > dados_resumidos.json

# Exportar como CSV
curl "http://localhost:5000/api/export?format=csv" -o dados_resumidos.csv

# Exportar com dados brutos completos (requer ALLOW_RAW_EXPORT=true)
curl "http://localhost:5000/api/export?format=json&include_raw=true" > dados_completos.json
```

---

## Pipeline de replicação

O pipeline em `replication_pipeline/` reproduce a metodologia do artigo em etapas auditáveis:

```
dados_completos.json  →  00  Anonimização  →  01  Seleção de atributos
                                                    ↓
                        04  KNN (artigo)  ←  03  KNN  ←  02  Matriz numérica
```

### Executar tudo de uma vez

```bash
cd replication_pipeline
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
python run_all.py
```

### Ou etapa por etapa

```bash
# 0. Anonimizar o dataset (remove nomes, visitorId, confidence)
python 00_prepare_anonymized_sample.py

# 1. Filtrar atributos conforme regras do artigo (Eq. 1, 4, 5)
python 01_filter_article_rules.py

# 2. Construir matriz numérica com rótulos naturais
python 02_build_numeric_matrix.py

# 3. Treinar e avaliar KNN — cenário A: atributos selecionados pela replicação
python 03_train_knn.py

# 4. Avaliar KNN — cenário B: atributos finais do artigo original
python 04_run_article_features.py
```

### Parâmetros da etapa 01

```bash
python 01_filter_article_rules.py --uniqueness-source value    # padrão (usa valores)
python 01_filter_article_rules.py --uniqueness-source duration # usa tempos
python 01_filter_article_rules.py --uniqueness-source either   # aprova se valor OU tempo passa
```

### Artefatos gerados

| Caminho | Descrição |
|---|---|
| `data/input/anonymous_fingerprints.json` | Dataset anonimizado |
| `data/intermediate/filtering/feature_selection.csv` | Estatísticas e resultado por feature |
| `data/intermediate/filtering/selected_features.json` | Lista de features selecionadas |
| `data/intermediate/matrix_filtered/` | Matriz numérica (cenário A) + mappings |
| `data/intermediate/matrix_article/` | Matriz numérica (cenário B) + mappings |
| `data/results/filtered_one_vs_rest/` | Resultados do cenário A |
| `data/results/article_one_vs_rest/` | Resultados do cenário B |
| `data/results/statistical_analysis_summary.csv` | Testes estatísticos pareados |
| `figures/` | Gráficos PNG (300 dpi) |

---

## Relatório estatístico (R)

O R Markdown em `replication_pipeline/replication_analysis_one_vs_rest.Rmd` gera um relatório HTML com tabelas e gráficos comparando os dois cenários.

### Instalar dependências

```r
install.packages(c("rmarkdown", "tidyverse", "jsonlite", "knitr", "scales"))
```

### Renderizar

```bash
cd replication_pipeline
Rscript -e "rmarkdown::render('replication_analysis_one_vs_rest.Rmd')"
```

### Figuras geradas em `figures/`

| Arquivo | Descrição |
|---|---|
| `fig_f1_score_por_k.png` | F1-score médio por K |
| `fig_acuracia_por_k.png` | Acurácia média por K |
| `fig_far_frr_melhor_k.png` | FAR e FRR no melhor K |
| `fig_sobreposicao_atributos.png` | Sobreposição de atributos entre artigo e replicação |
| `fig_motivos_exclusao.png` | Motivos de exclusão dos atributos |
| `fig_f1_por_participante.png` | F1-score por participante |

---

## Deploy em produção

### Opção 1 — Docker Compose em VPS (Recomendado para pesquisa)

```bash
# Na sua VPS (Ubuntu/Debian)
apt update && apt install -y docker.io docker-compose-plugin

git clone <repo> && cd fingerprint-research

cp .env.example .env
# Edite .env com valores de produção:
# - SECRET_KEY: string longa e aleatória
# - POSTGRES_PASSWORD: senha forte
# - CORS_ORIGINS: URL do seu frontend
# - VITE_API_URL: URL pública do seu backend

docker compose up -d --build
```

Acesse http://seu-ip:3000

### Opção 2 — Render (backend) + Vercel (frontend)

**Backend no Render:**

1. Crie uma conta em [render.com](https://render.com)
2. Novo serviço → Web Service → conecte o repositório
3. Root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `flask db upgrade && gunicorn run:app`
6. Adicione um banco PostgreSQL no Render
7. Configure as variáveis de ambiente no painel do Render

**Frontend na Vercel:**

1. Crie uma conta em [vercel.com](https://vercel.com)
2. Importe o repositório
3. Root directory: `frontend`
4. Build command: `npm run build`
5. Output directory: `dist`
6. Adicione a variável `VITE_API_URL` apontando para o backend no Render

### Opção 3 — Railway (backend + DB + frontend no mesmo lugar)

```bash
# Instale o CLI do Railway
npm install -g @railway/cli
railway login
railway init
railway up
```

Configure as variáveis no painel do Railway e adicione um plugin PostgreSQL.

---

## Cuidados éticos incorporados

| Aspecto | Implementação |
|---|---|
| **Consentimento explícito** | Coleta desabilitada no carregamento. FingerprintJS só é executado após o clique no botão, com checkbox de consentimento marcado e nome preenchido. |
| **Transparência** | Página explica o objetivo da pesquisa, o que é coletado, como será usado e o que NÃO é coletado. |
| **Minimização de dados** | IP não é armazenado em texto claro — apenas hash SHA-256 unidirecional. |
| **Sem exibição bruta** | O frontend nunca exibe o fingerprint bruto completo ao participante. |
| **Proteção do banco** | A rota `/raw` e a opção `include_raw` exigem variável `ALLOW_RAW_EXPORT=true`, desabilitada por padrão. |
| **Nomes fora da exportação** | A rota `/api/export` não inclui `participant_name` por padrão. |
| **Sem rastreamento silencioso** | Nenhuma chamada ao FingerprintJS fora do fluxo de consentimento explícito. |
| **Sem cookies de terceiros** | FingerprintJS OSS opera inteiramente no cliente, sem chamadas a servidores externos. |
| **CORS configurável** | Origem permitida definida por variável de ambiente, não hardcoded. |
| **Dados para publicação** | A versão pública dos dados usará identificadores anônimos (`participant_id` UUID), sem nomes reais. |

---

## Licença

Este projeto é desenvolvido exclusivamente para fins acadêmicos.  
Não deve ser utilizado para rastreamento, vigilância ou autenticação em produção.
