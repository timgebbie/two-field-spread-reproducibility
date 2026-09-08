# two-field-spread-reproducibility

Version: v0.0.0

Placeholder reproducibility repository for the **Two Field Spread Reproducibility Software** project and the numerical companion to the TwoFieldSpread theory paper.

This repository is intentionally minimal. It establishes the reproducibility structure only; `v0.0.0` contains no scientific implementation, generates no publication figures, and makes no numerical claim. Structure should be added only when an active release requires it.

## Planned release route

- **v1.0.0** — minimum theoretical plots and deterministic reduced simulations.
- **v2.0.0** — DTRW reaction-diffusion implementation.
- **v3.0.0** — integrated validation and paper-return gate.

## Placeholder validation

```bash
python scripts/run_all.py
python -m unittest discover -s tests -v
```

Scientific outputs remain disabled in `config/default.yaml` until the accepted theory-paper inputs are introduced at the start of `v1.0.0`.
