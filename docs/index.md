# CS Learning Wiki

My personal knowledge base. Browse a topic from the sidebar or jump in below.

## Topics

<div class="grid cards" markdown>

- :material-language-python: **[Python Fundamentals](python-fundamentals/index.md)**

    Core language features, idioms, and the standard library.

- :material-sitemap: **[System Design](system-design/index.md)**

    Scalable, reliable systems — building blocks and case studies.

- :fontawesome-brands-aws: **[AWS](aws/index.md)**

    Core services, patterns, and hands-on notes.

- :material-robot: **[AI Agent](ai-agent/index.md)**

    LLM-powered agents — tools, memory, and orchestration.

</div>

## How this wiki is organized

Each topic is a folder under `docs/`, and each folder has an `index.md` overview
plus one Markdown file per article:

```
docs/
├── index.md                    # this home page
├── tags.md                     # auto-generated tag index
├── python-fundamentals/
│   ├── index.md                # topic overview
│   └── variables-and-types.md  # an article
├── system-design/
│   └── index.md
├── aws/
│   └── index.md
└── ai-agent/
    └── index.md
```

### Add a new article

1. Create a `.md` file in the topic folder, e.g. `docs/aws/s3-basics.md`.
2. Add a line under that topic in `mkdocs.yml`'s `nav:`, e.g.
   `      - S3 Basics: aws/s3-basics.md`.
3. Optionally link it from the topic's `index.md` and add `tags:` front matter.

### Add a new topic

1. Create `docs/<new-topic>/index.md`.
2. Add a new top-level section in `mkdocs.yml`'s `nav:` mirroring the existing ones.

### What you can put in an article

Text, tables, fenced **code** (with syntax highlighting + copy button),
**diagrams** via Mermaid, and **callouts** via admonitions — see the
[template article](python-fundamentals/variables-and-types.md) for live examples.

## Edit locally

```bash
source .venv/bin/activate
mkdocs serve        # http://127.0.0.1:8000, live-reloads as you edit
```

Push to `main` and GitHub Actions rebuilds and deploys automatically.
