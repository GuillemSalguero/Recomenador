# CineMente — Natural Language Movie Recommender

> Final Degree Project · Grau en Enginyeria Informàtica · Universitat de Girona · June 2026  
> Author: **Guillem Salguero Montes**

CineMente is a movie recommendation system that understands natural language queries. Instead of filtering by genre or year, you can write *"a film that makes you think but isn't depressing"* and the system finds movies whose **critic reviews** match that experience — not just their metadata.

---

## Table of Contents

- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Retrieval strategies](#retrieval-strategies)
- [Evaluation](#evaluation)
- [Project structure](#project-structure)
- [Related repositories](#related-repositories)

---

## How it works

The key idea is using **Rotten Tomatoes critic reviews as a semantic bridge**. When you submit a query, the system compares it against what critics have written about each film — not against cold metadata like title, genre, or year. This allows it to capture tone, mood, and nuance that keyword search cannot.

The pipeline is built on a RAG (Retrieval-Augmented Generation) architecture with five interchangeable retrieval strategies, a hybrid BM25 + vector search core, and LLM-powered query understanding.

---

## Tech stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · shadcn/ui |
| User backend | Spring Boot 3 (Java 21) · JPA/Hibernate · JWT · BCrypt · PostgreSQL |
| AI engine | FastAPI · LangChain · ChromaDB · Sentence Transformers · BM25 |
| LLMs | Llama-3.3-70B · Llama-3.1-8B-Instant via Groq API |
| Database | Supabase (PostgreSQL) · ChromaDB (vector store) |

---

## Getting started

### Prerequisites

- Python 3.10+
- Java 21 + Maven
- Node.js 18+
- A `.env` file with `GROQ_API_KEY` and Supabase credentials
- ChromaDB pre-indexed with the Rotten Tomatoes dataset (see `src/indexing/`)

### 1. AI recommendation service (FastAPI)

```bash
pip install -r requirements.txt
python -m uvicorn src.app:app --reload --port 8001
```

### 2. User backend (Spring Boot)

Configure `application.yml` with your Supabase URL and JWT secret, then:

```bash
mvn spring-boot:run
```

### 3. Frontend (React)

```bash
npm install
npm run dev
```

Once all three services are running, open `http://localhost:5173`.

---

## Retrieval strategies

Five independent and composable strategies have been implemented:

**Hybrid** — Combines dense semantic search (ChromaDB + cosine similarity) with sparse lexical search (BM25 over the top 200 semantic candidates). Results are merged with Reciprocal Rank Fusion (RRF, weights 0.7/0.3).

**Self-Querying** — Uses `Llama-3.3-70B` to extract structured filters from the query (genre, director, year, Tomatometer, runtime) and apply them before the vector search. Enforces determinism with `temperature=0` and few-shot prompting.

**Multi-Query** — Uses `Llama-3.1-8B` to generate 5 semantic reformulations of the original query, runs them in parallel, and deduplicates results. Effective for abstract or emotional queries.

**Parent Retrieval** — Aggregates individual review fragments at the movie level, building a consolidated document with up to 8 reviews per title. Highest corpus coverage in evaluation (120 unique titles).

**Combined** *(experimental)* — Chains Self-Querying and Multi-Query: filters restrict the search space, then reformulations explore it semantically. Best overall on queries that mix explicit constraints with tonal intent.

---

## Evaluation

Evaluated across 12 reference queries in 4 categories: abstract, metadata-explicit, niche, and contradictory.

| Module | Unique titles | ILD avg | Strengths |
|--------|:---:|:---:|---|
| Self-Query | 89 | 0.17 | Explicit metadata filters |
| Hybrid | 117 | 0.73 | Precision / coverage balance |
| Multi-Query | 68 | 0.76 | Abstract / emotional queries |
| Combined | 94 | 0.76 | Mixed constraint + tone queries |
| Parent | 120 | 0.68 | Maximum corpus coverage |

Three metrics were used: **LLM-as-a-Judge** (Llama-3.3-70B scores relevance 0–100), **Algorithm Retrieval** (unique titles recovered), and **Intra-List Diversity / ILD** (variety within a result list, combining genre 50% + director 30% + year 20%).

---

## Project structure

```
src/
├── app.py                    # FastAPI entry point
├── retrievers/
│   ├── hybrid.py
│   ├── self_query.py
│   ├── multi_query.py
│   ├── parent_retrieval.py
│   └── combined.py
├── indexing/                 # ChromaDB indexing scripts
└── evaluation/               # Benchmark scripts (LLM-as-a-Judge, ILD, retrieval coverage)
```

---

## Related repositories

| Service | Repository |
|---------|-----------|
| Frontend (React) | https://github.com/GuillemSalguero/cinementeWs |
| User backend (Spring Boot) | https://github.com/GuillemSalguero/cinemente-recommender |

---

*Academic project — Universitat de Girona, June 2026.*
