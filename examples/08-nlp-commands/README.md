# NLP (Natural Language Processing) Examples

This directory contains examples of using the Rebuild NLP service to convert natural language commands to DSL/CLI commands.

## Running NLP Commands

### Parse a natural language command:
```bash
python3 -m rebuild nlp "analyze code for duplicates"
```

### Convert to DSL:
```bash
python3 -m rebuild nlp "analyze code for duplicates" --to-dsl
```

### Convert to CLI args:
```bash
python3 -m rebuild nlp "analyze code for duplicates" --to-cli
```

## Supported Natural Language Patterns

### Walk Commands
- "walk last 7 days"
- "test history for 30 days"
- "analyze git history"
- "walk repo /path/to/repo"

### Analyze Commands
- "analyze code for duplicates"
- "scan for complexity"
- "check code quality"
- "detect duplicate code"
- "analyze service dependencies"

### Evolution Commands
- "generate evolution timeline"
- "show code evolution"
- "visualize dependency graph"
- "timeline of code changes"

### Auto-PR Commands
- "create PR with analysis"
- "generate pull request"
- "auto PR from analysis"
- "create merge request"

### Accelerator Commands
- "run fast analysis"
- "accelerate testing"
- "quick scan"

### Restore Commands
- "restore endpoint"
- "recover endpoint"
- "recreate endpoint"

### Serve Commands
- "serve reports"
- "start dashboard"
- "show reports"

## Examples

### Example 1: Walk command
```bash
python3 -m rebuild nlp "walk last 7 days" --to-dsl --to-cli
```

Output:
```
Zinterpretowana komenda: walk
  Confidence: 0.33
  Parameters: {'days': '7'}

DSL: walk days:7
CLI args: walk --days 7
```

### Example 2: Analyze duplicates
```bash
python3 -m rebuild nlp "analyze code for duplicates" --to-dsl --to-cli
```

Output:
```
Zinterpretowana komenda: analyze
  Confidence: 0.33
  Parameters: {'type': 'code'}

DSL: analyze type:code
CLI args: analyze --type code
```

### Example 3: Create PR
```bash
python3 -m rebuild nlp "create PR with analysis" --to-dsl
```

Output:
```
Zinterpretowana komenda: auto_pr
  Confidence: 0.33
  Parameters: {}

DSL: auto_pr
```

## Programmatic Usage

```python
from rebuild.application.services.nlp_service import NLPService

nlp = NLPService()

# Parse natural language
command = nlp.parse("analyze code for duplicates")
print(f"Intent: {command.intent.value}")
print(f"Parameters: {command.parameters}")
print(f"Confidence: {command.confidence}")

# Convert to DSL
dsl = nlp.to_dsl(command)
print(f"DSL: {dsl}")

# Convert to CLI args
cli_args = nlp.to_cli_args(command)
print(f"CLI: {' '.join(cli_args)}")
```

## Limitations

- NLP uses pattern matching, not full AI/ML
- Confidence scores indicate how well the pattern matched
- Complex sentences may not be parsed correctly
- For best results, use simple, direct commands
