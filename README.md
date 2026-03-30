# Cloud AI Ops Core

Cloud AI Ops Core contains the ingestion and orchestration logic behind the public knowledge repository.

## Purpose

This repo handles four stages:

1. `extract agent`: fetch post/blog/repo content and gather image inputs
2. `classify agent`: use Ollama to detect content type, category, subcategory, and tools
3. `verify agent`: search the web, prefer official sources, and check post accuracy
4. `enhance agent`: use Ollama plus verified context to improve the note
5. `publish agent`: write the final markdown into the public repo and optionally commit and push it

The public reading repo is separate:

- public repo: `cloud-ai-ops-knowledge`
- core repo: `cloud-ai-ops-core`

## Run

```bash
python3 run_pipeline.py \
  --url "https://example.com/post" \
  --public-repo ../cloud-ai-ops-knowledge \
  --classifier-model llama3:latest \
  --verifier-model deepseek-r1:latest
```

If you want image understanding for posts that contain screenshots or visuals, install a local Ollama vision model and pass it with `--vision-model`.

## Design

The public repo is output-only. All logic stays here:

- Ollama model calls
- web verification search
- image-aware classification
- official-source cross-check support
- category/subcategory path selection
- final publishing

For authenticated LinkedIn extraction, set `LINKEDIN_COOKIE` in your environment before running the pipeline.
