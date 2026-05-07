# Installation

> See also: [Quick Start](quickstart.md) · [Configuration](configuration.md) · [CLI Reference](../reference/cli.md)

## Requirements

- Python **3.11+**
- Git installed and on `PATH`
- Docker / Docker Compose (only needed for `--deploy docker-compose`)

## Install from PyPI

```bash
pip install rebuild
```

## Optional extras

| Extra | Installs | Use when |
|---|---|---|
| `screenshots` | Playwright (Chromium) | You want screenshot capture |
| `tui` | Textual | You want the interactive TUI |
| `semantic` | sentence-transformers | You need semantic code similarity |
| `full` | All of the above | Full feature set |

```bash
# Just screenshots
pip install "rebuild[screenshots]"
playwright install chromium

# Full install
pip install "rebuild[full]"
playwright install chromium
```

## Install from source

```bash
git clone https://github.com/semcod/resplit
cd resplit
pip install -e ".[dev]"
```

## Verify installation

```bash
rebuild version
# rebuild v0.1.23
```
