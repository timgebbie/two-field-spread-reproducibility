# Two Field Spread Reproducibility

**v0.3.0 — minimal two-density DTRW core.** A numerical companion to the TwoFieldSpread paper and letter, built from the accepted v0.0.0 scaffold.

## Contents

- [Numerical model](#numerical-model)
- [Reproduce](#reproduce)
- [Saved state](#saved-state)
- [Verification and limits](#verification-and-limits)
- [Next outputs](#next-outputs)

## Numerical model

The code evolves nonnegative bid and ask densities on a uniform log-price grid in operational time. Each update uses one frozen state for nearest-neighbour diffusion, cancellation and symmetric reaction. Earlier executions generate causal opposite-side replenishment. Residual pending inventory sets placement quotes; external and completion sources use those quotes. A capped event then consumes the available side density in price priority. Threshold crossings determine observed bid, ask, midpoint and spread.

The implemented baseline uses equal transport/cancellation coefficients, geometric completion weights, prescribed fixed reservoirs and a stationary initial field with empty completion prehistory. The numerical step, a child-order event and calendar time are distinct. The [algorithm and conventions](provenance/ALGORITHM.md) specify the update order, stock samples, source normalization, execution cells and volume budget.

## Reproduce

From the extracted repository directory in Windows PowerShell, with Python 3.11+:

```powershell
$ErrorActionPreference = 'Stop'
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed' }
$Python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $Python -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Installation failed' }
& $Python scripts/run_all.py
if ($LASTEXITCODE -ne 0) { throw 'Core verification failed' }
```

Only NumPy is required. The tested environment is Python 3.12.14 and NumPy 2.3.5 on Linux. Windows verification remains a later milestone.

The route runs 14 numerical tests, relaxes a positive-reaction reference, and saves a no-event control plus a three-child execution fixture. This fixture checks that the numerical components work together; its parameters are not the final paper experiment. No publication figure or video is generated in v0.3.0.

## Saved state

`config/core-v0.3.0.json` is the complete fixture configuration. The execution file specifies child times and volumes in operational units; times must coincide with positive update endpoints. The runner never silently changes the step.

| Saved file | Content |
|---|---|
| `outputs/*-v0.3.0.csv` | Per-update quotes, spread, source geometry, requested/actual/unfilled volumes, pending stocks, completed flows and volume diagnostics |
| `outputs/*-snapshots-v0.3.0.csv` | Exact update/time/phase mapping for retained states |
| `outputs/*-states-v0.3.0.npz` | Initial/final densities and selected incoming, pre-consumption and post-consumption states; source and removal increments |
| `outputs/verification-v0.3.0.json` | Test count, stationary residual and run-level numerical checks |
| `outputs/data-manifest-v0.3.0.json` | Configuration, code, test and output hashes |

The code retains `config/`, `figures/`, `functions/`, `outputs/`, `provenance/`, `scripts/` and `tests/`. `figures/` is reserved for plots of the numerical experiments.

## Verification and limits

Tests address the discrete diffusion/cancellation eigenmode, frozen reaction, reservoir flux and volume accounting, positivity rejection, source support, causal completion, immediate completion, preservation of completion time under step refinement, buy/sell reflection, execution caps, threshold exits, stationary drift and a reaction-off stationary reference.

Analytic formulas are used only as solver benchmarks. The earlier standalone theory figures and formula plotting route have been removed. They added no simulation evidence to the paper or letter.

The current nodal source and execution conventions require grid, step and domain studies before interpreting price-impact curves. A discontinuous source edge has first-order grid error under the implemented nodal support convention. Positive-reaction stationary residuals and exact accounting do not establish convergence of the final meta-order experiment. Missing, ambiguous, ill-conditioned or unordered price crossings stop the calculation; densities and spreads are not clipped to manufacture valid outputs.

## Next outputs

v0.4.0 will produce simulated density evolution, bid/ask/midpoint/spread and market-maker time series, and matched replenishment/placement controls. A short video will use the same saved trajectory. An initial profile can appear as a numerical snapshot; a separate analytic figure is not a release requirement. v0.5.0 assesses convergence and scientific claims before supplementary material and final reproduction work toward v1.0.0.

A future v1.1.0 study will consider how market-maker spread dynamics influence meta-order response and impact. Its required event/state information is already retained.

The numerical prototype is [correlation-emergence v2.2.0](https://github.com/timgebbie/correlation-emergence-reproducibility/releases/tag/v2.2.0). This is a clean, thinned implementation for two sides of one market; it has no runtime dependency on that repository. [Source provenance](provenance/SOURCES.md) records the exact antecedent and paper versions.
