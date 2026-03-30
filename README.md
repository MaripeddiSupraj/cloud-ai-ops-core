# Cloud AI Ops Core

Cloud AI Ops Core contains the ingestion and orchestration logic behind the public knowledge repository.

## Purpose

This repo handles three stages:

1. `classify agent`: detect content type, categories, tools, and source context from a link
2. `enhance agent`: structure the note and attach official-source references for cross-checking
3. `publish agent`: write the final markdown into the public repo and optionally commit and push it

The public reading repo is separate:

- public repo: `cloud-ai-ops-knowledge`
- core repo: `cloud-ai-ops-core`

## Run

```bash
python3 run_pipeline.py --url "https://example.com/post" --public-repo ../cloud-ai-ops-knowledge
```

Write and push to the public repo in one run:

```bash
python3 run_pipeline.py \
  --url "https://example.com/post" \
  --public-repo ../cloud-ai-ops-knowledge \
  --push-public
```

## Design

The code stays intentionally simple and dependency-free:

- standard-library URL fetching
- rule-based classification
- official-source hint mapping
- markdown publishing into the public repo

This keeps the system easy to run, audit, and improve later with a stronger model-backed enhancer if needed.

