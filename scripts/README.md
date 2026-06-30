# scripts/

Runnable Python snippets that accompany the wiki articles in `docs/`. Use them
to experiment with and verify the examples while reading.

These scripts live **outside** `docs/`, so they are version-controlled but
**not** published to the site.

## Layout

Mirror the `docs/` topic folders so each script maps to an article:

```
scripts/
└── python-fundamentals/
    └── concurrency-01.py        # ↔ docs/python-fundamentals/concurrency-01-intro.md
```

## Running

```bash
source .venv/bin/activate        # the project virtualenv
python scripts/python-fundamentals/concurrency-01.py
```

If a script needs third-party packages, add them to `requirements-dev.txt`
(create it) and `pip install -r requirements-dev.txt` — keep them separate from
the site's `requirements.txt`.
