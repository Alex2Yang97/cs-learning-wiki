# My Knowledge Wiki

A personal knowledge base built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) and published to GitHub Pages.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve   # http://127.0.0.1:8000
```

## Adding content

1. Add a Markdown file under `docs/`.
2. Register it in the `nav:` list in `mkdocs.yml`.
3. Commit and push to `main`.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the
site and deploys it to GitHub Pages. One-time setup: in the repo, go to
**Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
