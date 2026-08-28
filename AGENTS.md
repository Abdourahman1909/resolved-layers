# Repository instructions for AI agents

Before answering project-specific questions or changing files:

1. Read `docs/PROJECT_MEMORY.md` completely. It is the durable memory backbone for this repository.
2. Read `CONTEXT.md` and use its canonical domain language.
3. Read relevant files in `docs/adr/` before proposing a conflicting architectural decision.
4. Treat `docs/PRD.md` as an evolving draft until its open decisions are resolved.
5. Keep this repository independent from the parent training repository. Do not copy training experiments, datasets, reports, or the Streamlit interface into it.
6. Each Prediction Run fixes one validated Model Package and its Inference Contract. The first release ships only the current package; later Model Library support must accept controlled packages, never arbitrary model files or folders.
7. Do not commit organizer data, trained model weights, mappings derived from restricted data, or example organizer rows until publication permission is confirmed.
8. Explain planned changes before modifying important product, architecture, or model-integration files.
9. The accepted desktop stack is PySide6 with a custom QML/Qt Quick presentation layer and a Python inference core. Do not replace it or fall back to generic Qt widget styling without an explicit decision.

Maintain context actively:

- Update `docs/PROJECT_MEMORY.md` whenever a milestone, project stage, important fact, or durable decision changes.
- Update `CONTEXT.md` immediately when domain terminology is resolved. Keep it a glossary, not a technical specification.
- Add an ADR only for decisions that are costly to reverse, surprising without context, and chosen through a genuine trade-off.
- At the end of substantial work, update **Where work stopped** with completed work, unresolved items, and the next question or implementation step.
