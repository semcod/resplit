# TODO: rebuild Roadmap

Future improvements and features for the Code Evolution Intelligence Engine.

## Phase 5: Automated Refactoring & AI Assistance
- [x] **Automated Patching**: Implement logic to automatically execute recommended refactors (Initial RefactorExecutor).
- [ ] **LLM Integration**: Use LLMs to generate "Refactor PRs" with high-level summaries.
- [ ] **Semantic Embeddings**: Integrate `sentence-transformers` for true semantic similarity detection in `duplication_engine`.

## Phase 6: Infrastructure Hardening
- [x] **Adapter Pattern**: Fully isolate `subprocess` and `httpx` calls into `infrastructure/` adapters.
- [ ] **Multi-Repo Support**: Enable analysis across multiple repositories for cross-project duplication detection.
- [ ] **Incremental Walking**: Optimize `rebuild walk` to only analyze changes since the last run.

## Phase 7: UI/UX Evolution
- [ ] **Graph Visualization**: Export `service_graph` to interactive HTML/D3.js visualizations.
- [ ] **TUI Refactor**: Extract domain logic from `interfaces/tui.py` into shared services.
- [ ] **Real-time Monitoring**: Show live analysis results in the dashboard during `rebuild walk`.

## Refinement
- [ ] **Better CC Heuristics**: Fine-tune the `TruthRanker` score weights based on larger real-world data.
- [x] **Language Support**: Expand AST/Regex analysis beyond Python (Added JS/TS support).
