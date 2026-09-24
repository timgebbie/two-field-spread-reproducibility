# Two Field Spread Reproducibility

**v0.4.1 — numerical pilot, execution tape and compatibility audit.** A clean, reduced DTRW implementation of the two side-density model in the TwoFieldSpread paper and letter. The numerical results below are preliminary; convergence assessment and longer two-sign experiments are the next stage. The density core and existing numerical trajectories are unchanged from v0.4.0.

The model evolves bid and ask densities in operational time using nearest-neighbour diffusion, cancellation and symmetric reaction. A finite buy programme consumes the ask side. Executed volume initiates causal replenishment on the bid side; residual pending inventory determines placement width and centre. Inward density thresholds determine observed bid, ask, midpoint and spread. [Algorithm and conventions](provenance/ALGORITHM.md) specify the chronology, inventories, execution cap and volume budgets.

## Focused numerical outputs

![Density evolution](figures/density-v0.4.1.png)

**F2. Density evolution.** Nine snapshots of the same delayed-completion, moving-placement simulation. Six buy children of volume 0.05 arrive at u=1, 1.4, 1.8, 2.2, 2.6 and 3. Blue/red are bid/ask densities; grey is the numerically relaxed initial field. Coloured dotted lines are placement quotes q; dashed lines are observed threshold prices p. The horizontal dotted line is the fixed density threshold 0.1. Pre/post pairs show the actual execution impulse. All panels have fixed axes; the displayed log-price window is [-8,8] within the simulated domain [-12,12].

![Prices and market-maker state](figures/timeseries-v0.4.1.png)

**F3. Same-run time series.** Observed quotes and actual fill-weighted execution log prices (orange points); observed spread and placement width; post-event pending stock; signed post-event inventory; cumulative executed and completed volumes; placement centre. The shaded interval spans the buy programme. P denotes stock after execution, whereas placement uses Q after old-cohort delivery and before the current execution. Panel (e) displays integrated flows in volume units, not impulse heights divided by a numerical time step. Midpoint is the arithmetic midpoint in log price.

![Matched controls](figures/controls-v0.4.1.png)

**F4. Matched controls.** Delayed completion with moving placement; completion at the next update; delayed completion with fixed placement. Every case executes the same six child volumes, totalling 0.3. The midpoint response subtracts the shared no-event trajectory; their empty-pending no-event equations coincide. Delayed cases have overlapping pending-stock curves. The immediate control retains each new child until the next update, producing narrow post-event spikes. These are pilot comparisons, not a systematic impact study.

[![Video preview](figures/video-poster-v0.4.1.png)](figures/density-v0.4.1.mp4)

**V1. [24-second profile video](figures/density-v0.4.1.mp4).** The same stored trajectory, fixed axes and explicit operational-time/phase labels, with spread and pending-stock cursors. Stored states are held between frames; each child has consecutive pre/post frames. No interpolation of densities across an impulse is used. Grey density lines retain the initial reference.

PNG and PDF versions of the three figures are in `figures/`. There is no standalone theoretical-figure requirement.

## Reproduce

Python 3.12 is the controlled environment. Install FFmpeg with the libx264 encoder and put `ffmpeg` on PATH. NumPy and Matplotlib are pinned in `pyproject.toml`.

From the repository directory, Linux/macOS:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/run_all.py
```

Windows PowerShell, from the repository directory with Python installed:

```powershell
$ErrorActionPreference = 'Stop'
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed' }
$Python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $Python -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Installation failed' }
ffmpeg -version
if ($LASTEXITCODE -ne 0) { throw 'Install FFmpeg with libx264 and add it to PATH' }
& $Python scripts/run_all.py
if ($LASTEXITCODE -ne 0) { throw 'Reproduction failed' }
```

The command runs 20 focused tests, stationary initialization, the three event cases, one no-event control and a coarser mesh pilot, then produces all figures and the video. A repeat uses the same command. `python scripts/run_all.py --render-only` verifies the configuration/code/data hashes and redraws from saved states without solving. A changed input requires the complete route. The tested runtime is Python 3.12.14, NumPy 2.3.5 and Matplotlib 3.10.8 on Linux; Windows execution remains a later milestone.

## Configuration and retained data

`config/experiments-v0.4.1.json` is the sole experiment configuration: explicit model parameters, child programme, case overrides, mesh pilot, output samples, snapshot phases, video settings and numerical tolerances. Parameters are dimensionless and illustrative, with no empirical calibration. External lit and latent amplitudes/lengths are equal in this pilot, so their combined source is constant outside the placement edges. Completion time is 1 operational unit in the delayed cases.

| Directory | Active content |
|---|---|
| `config/` | One complete experiment configuration |
| `functions/` | Core recurrence, experiment driver, execution/statistic observations, renderer |
| `scripts/` | One full-run entry point |
| `tests/` | Two focused test files: core and observations |
| `outputs/` | Scalar/event/trade/fill CSVs, density NPZ and indices, verification/runtime records and hashes |
| `figures/` | Three PNG/PDF pairs, one MP4 and its poster |
| `provenance/` | Algorithm/equation mapping, draft LaTeX/PDF supplement, lineage audit and source identities |

The density archive contains the numerical fields and the incoming/pre/post event states, removal profiles and separate source increments. Scalar data retain requested/actual/unfilled volumes, observed and placement quotes, both inventory samples, cumulative flows and source geometry. `verification-v0.4.1.json` reports extrema checked over **every** update, despite the smaller saved plotting samples. The mesh-pilot CSV is numerical verification evidence and has no extra figure.

## Verification and current limits

The tests cover the discrete eigenmode, frozen reaction, reservoir flux/budgets, positivity rejection, support normalization, causal opposite-side completion, next-update completion, fixed physical completion time under refinement, buy/sell reflection, capped execution, quote selection/failure, stationary drift and an independent reaction-off stationary solution. The quote diagnostic follows the paper's supremum/infimum rule when multiple crossings occur; selected-crossing slope, reservoir and contact checks remain active.

For this pilot, all three event cases execute 0.3 within floating-point tolerance. Maximum field-budget and completion-ledger discrepancies are below 4.3e-15 and 2.1e-15 respectively. The no-event field drift is below 9.5e-9. These accounting checks do not establish convergence.

The joint coarse/fine change, (dx,du)=(0.1,0.002) to (0.05,0.001), gives maximum sampled differences of 0.07778 in spread and 0.02392 in midpoint. Source supports and price-priority execution are nodal and discontinuous. In particular, initial placement edges lie on grid nodes: a small outward displacement excludes those source nodes, including late in recovery. The visible finite-grid late spread offset must not be interpreted as permanent impact. No source smoothing or altered field equation has been introduced to remove it.

v0.5.0 will assess grid, time-step, domain, grid-phase/threshold and event resolution, then the requested market-maker and LMF correlation experiments before scientific acceptance. The [draft supplementary algorithms](provenance/supplement-v0.4.1.pdf) distinguish the implemented steps from planned diagnostics and future memory/clock extensions. A future v1.1.0 study will examine systematic spread-dependent meta-order impact scaling.

## Aggregate agents and the market-maker mechanism

The software evolves aggregate order densities with an order-level DTRW interpretation. It does not currently simulate individual traders, strategies or wealth. Lit/latent sources represent aggregate supply, aggressive executions are explicit inputs, and pending completion controls market-maker placement. Chartist or fundamentalist behaviour is not automatically encoded by a static source. No additional trader population is needed for the present mechanism tests.

Round-trip completion is a **completion-equivalent source closure**: its probabilities are assumed within the delivery/placement law. It is not an explicit second trade or a profit calculation. Every executed child in this pilot is attributed to the aggregate market-making sector. The exact volume ledger does not establish financial equilibrium. The imposed positive placement floor also means the baseline spread is not evidence of emergence from zero standoff.

The next focused comparison should show balanced buy/sell activity with substantial total pending exposure but small signed inventory. Separate width-only and centre-only feedback controls identify the two effects; the existing jointly fixed control does not. Show placement quotes and observed quotes together, pending modes, completed/initiated volume and recovery after flow stops. Reuse F3/F4 and the density video for this explanation.

## Trade tape and correlation targets

The new trade/fill CSVs retain actual executions, parent IDs, true aggressor signs, pre/post quotes, log midpoint, spread and market-maker state. Execution log price follows v2.0.0: the fill-volume-weighted log coordinate. Its exponent is stored separately from arithmetic price VWAP. Consecutive trade returns and absolute returns are included; first returns are missing. Completion delivery and aggregate reaction do not create synthetic trade prints.

The six current children are all buys. They cannot establish LMF persistence or a sign ACF. A planned aggregate order-splitting generator and an independent-sign null will drive longer density simulations with recorded seeds, matched volumes/rates and independent path groups. Persistent order flow is a stated input mechanism whose transmission to price and spread is tested; it is not claimed to arise spontaneously from RD.

| Target | Contents | Status |
|---|---|---|
| F2, F3, F4, V1 | Density snapshots; prices/MM state including execution prices; matched controls; profile video | Pilot produced |
| F5 | Aligned price/spread/sign paths; ACFs of true signs, mid-log increments, execution-log increments, their absolute increments, and spread | Planned; no LMF result yet |
| F6 | Lagged sign/return, sign/spread-change, mid/trade-return, mid-return/spread-change and magnitude/spread cross-correlations | Planned |

Raw price paths remain available. Absolute positive price levels add no information; absolute increments address persistence in movement size. Price-level ACFs would be descriptive, not evidence of long memory. The estimator follows the prior executable overlapping-pair Pearson convention, with pair counts and explicit lag direction. A zero-variance series is undefined. Fixed reservoirs and fixed valuation centre can produce mean reversion; white returns, volatility clustering and square-root impact are hypotheses, not enforced outputs.

## DTRW compatibility

The shared Markov transport operator was checked against exact v2.0.0 source. The present paper uses Euler cancellation; the prototype uses an exponential survivor. Their finite-step difference, event chronology and boundary/source differences are documented in the [algorithm mapping](provenance/ALGORITHM.md). This is compatible lineage, not complete finite-step equality. The observable conventions and nondegenerate ACF estimator agree with the prior executable implementation.

Future Sibuya transport needs a transport history and a stated treatment of reaction, births and removal. Keep it separate from order-sign memory, the finite-mean round-trip delay and calendar subordination. No fractional or calendar extension is implemented yet. The supplement records the raw-kernel, single-survival, scaling and previous-completed-state conventions to preserve.

The numerical/presentation prototype is [correlation-emergence v2.2.0](https://github.com/timgebbie/correlation-emergence-reproducibility/releases/tag/v2.2.0). This independent implementation represents the two sides of one market and has no runtime dependency on the prototype. [Source provenance](provenance/SOURCES.md) records the original scaffold and exact paper/prototype versions. Manuscripts and recovery administration remain outside this source tree.
