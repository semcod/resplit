# Plugins

> See also: [Architecture](../architecture.md#plugin-system) · [CLI Reference](../reference/cli.md#rebuild-plugins)

`rebuild` supports custom **scanners** and **reporters** via Python package entry points.

## Built-in plugin groups

| Group | Interface | Purpose |
|---|---|---|
| `rebuild.scanners` | `BaseScanner` | Analyse a repository path, return findings |
| `rebuild.reporters` | `BaseReporter` | Consume walk results, produce artefacts |

## Writing a scanner

```python
# my_package/scanners.py
from pathlib import Path
from rebuild.plugins.base import BaseScanner, ScanResult

class SecurityScanner(BaseScanner):
    name = "security"
    description = "Scan for hardcoded secrets"

    def scan(self, path: Path, **kwargs) -> ScanResult:
        findings = []
        for py in path.rglob("*.py"):
            text = py.read_text(errors="ignore")
            if "password = " in text.lower():
                findings.append({"file": str(py), "issue": "possible hardcoded password"})
        return ScanResult(
            scanner=self.name,
            path=path,
            findings=findings,
            summary=f"{len(findings)} potential issues found",
        )
```

## Writing a reporter

```python
# my_package/reporters.py
from pathlib import Path
from typing import Any, List
from rebuild.plugins.base import BaseReporter

class SlackReporter(BaseReporter):
    name = "slack"
    description = "Send walk summary to Slack"

    def report(self, results: List[Any], output_dir: Path, **kwargs) -> None:
        import httpx
        webhook = kwargs.get("webhook_url", "")
        total = len(results)
        ok = sum(1 for r in results if r.deploy_success)
        httpx.post(webhook, json={"text": f"rebuild: {ok}/{total} days healthy"})
```

## Registering via entry points

In your package's `pyproject.toml`:

```toml
[project.entry-points."rebuild.scanners"]
security = "my_package.scanners:SecurityScanner"

[project.entry-points."rebuild.reporters"]
slack = "my_package.reporters:SlackReporter"
```

After `pip install my_package`, plugins appear in:

```bash
rebuild plugins
```

## Programmatic registration

```python
from rebuild.plugins import PluginRegistry
from my_package.scanners import SecurityScanner

registry = PluginRegistry()
registry.register_scanner("security", SecurityScanner)

result = registry.get_scanner("security")().scan(Path("/my/repo"))
print(result.summary)
```
