# rebuild Usage Guide

This guide covers step-by-step usage of the Code Evolution Intelligence Engine.

## 1. Installation
```bash
pip install rebuild
playwright install chromium # for screenshots
```

## 2. Initialization
Bootstrap your project with a default configuration:
```bash
rebuild init
```
This generates:
- `rebuild.yaml`: Pipeline and deployment settings.
- `.env`: API keys for AI features (OpenRouter).

## 3. Historical Analysis (The Walk)
Analyze the last 30 days of git history:
```bash
rebuild walk . --days 30 --deploy auto
```
For testing without full deployment:
```bash
rebuild walk . --days 30 --dry-run
```

## 4. Code Intelligence (Queries)
### Duplication Detection
Find structural clones in Python and JS/TS:
```bash
rebuild analyze duplicates . --min-lines 5
```

### Architecture Graph
Export an interactive D3.js dependency map:
```bash
rebuild analyze services --export
```

### Truth Discovery
Find the most stable historical version of a function:
```bash
rebuild analyze truth path/to/file.py my_function
```

## 5. Refactoring (Commands)
Generate a prioritized refactor plan with AI executive summary:
```bash
rebuild refactor plan . --ai
```

Automatically execute simple refactors:
```bash
rebuild refactor execute .
```

Generate a professional Pull Request description:
```bash
rebuild refactor pr .
```

## 6. Visualization
View the health timeline and quality metrics dashboard:
```bash
rebuild dashboard --repo .
```
Launch the interactive TUI:
```bash
rebuild tui
```
