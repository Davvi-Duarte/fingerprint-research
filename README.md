# Browser Fingerprinting Research

Replicação metodológica adaptada do artigo:

> **"Web user identification based on browser fingerprints using machine learning methods"**  
> Salomatin, Iskhakov & Iskhakova

Aplicação web para coleta consentida de browser fingerprints em ambiente acadêmico controlado.  
Os dados coletados serão usados para reprodução parcial do experimento com algoritmo KNN.

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
10. [Deploy em produção](#deploy-em-produção)
11. [Cuidados éticos incorporados](#cuidados-éticos-incorporados)

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

### Passo 3 — Pré-processamento em Python (exemplo)

```python
import json
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Carregue os dados exportados
with open("dados_completos.json") as f:
    data = json.load(f)

records = data["records"]

# Extraia features dos components do FingerprintJS
rows = []
for r in records:
    components = r.get("components", {}) or {}
    row = {
        "participant_id": r["participant_id"],
        "visitor_id": r.get("visitor_id"),
        "duration_total_ms": r.get("duration_total_ms"),
        # Extraia atributos relevantes dos components
        "platform": components.get("platform", {}).get("value"),
        "timezone": components.get("timezone", {}).get("value"),
        "language": components.get("languages", {}).get("value"),
        "screen_resolution": str(components.get("screenResolution", {}).get("value")),
        "color_depth": components.get("colorDepth", {}).get("value"),
        "hardware_concurrency": components.get("hardwareConcurrency", {}).get("value"),
        # Adicione outros atributos conforme necessário
    }
    rows.append(row)

df = pd.DataFrame(rows)

# Encode categóricos
le = LabelEncoder()
for col in df.select_dtypes(include="object").columns:
    if col != "participant_id":
        df[col] = le.fit_transform(df[col].astype(str))

# Prepare X e y para KNN
X = df.drop(columns=["participant_id"])
y = df["participant_id"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

knn = KNeighborsClassifier(n_neighbors=3)
knn.fit(X_train, y_train)
print(f"Acurácia KNN: {knn.score(X_test, y_test):.2%}")
```

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
