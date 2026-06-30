# My Knowledge Wiki

Welcome to my personal knowledge base. This site is built with
[MkDocs](https://www.mkdocs.org/) and the
[Material](https://squidfunk.github.io/mkdocs-material/) theme, and published
to GitHub Pages.

## How to add a page

1. Create a new Markdown file under `docs/`, e.g. `docs/python-tips.md`.
2. Add it to the `nav:` section in `mkdocs.yml` so it shows in the sidebar.
3. Commit and push — the GitHub Actions workflow rebuilds and deploys the site.

## Things you can use in pages

!!! tip "Callouts"
    Use admonitions for notes, tips, and warnings.

```python
# Code blocks get syntax highlighting and a copy button.
def hello():
    print("hello, wiki")
```

- [x] Task lists
- [ ] ...are supported too
