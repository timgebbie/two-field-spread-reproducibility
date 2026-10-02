# Two Field Spread Reproducibility

Reproducibility software for the forthcoming preprint **A Finite Bid–Ask Spread from Replenishment Displaced from the Quote**, by **Christopher Angstmann, Derick Diana and Tim Gebbie**.

**v0.6.0 — documentation consolidation.** The finite two-density DTRW mechanism and matched market-maker comparisons are accepted for qualitative and bounded quantitative interpretation at the retained resolution. F2/F3/F4 and V1 fall within that scope; F5/F6 remain diagnostic with unresolved spatial sensitivity. The v0.5.6 numerical source, configuration, arrays, diagnostics, plots and video are unchanged. The Markov DTRW core is unchanged from v0.4.1.

[Figures](#focused-numerical-outputs) · [Reproduce](#reproduce) · [Assessment](#accepted-finite-grid-result) · [Algorithm](provenance/ALGORITHM.md) · [Supplement](provenance/supplement-v0.6.0.pdf) · [Sources](provenance/SOURCES.md)

Two densities evolve in operational time by nearest-neighbour diffusion, cancellation and symmetric reaction. Aggressive executions initiate causal opposite-side replenishment. Total pending stock sets placement width; signed pending stock sets its centre. Inward density thresholds define the observed bid, ask, log midpoint and spread. A buy consumes ask liquidity and initiates bid replenishment; a sell consumes bid liquidity and initiates ask replenishment.

## Focused numerical outputs

![Density evolution](figures/density-v0.5.6.png)

**F2. Density evolution.** Nine snapshots from six buys of volume 0.05 at u=1,1.4,1.8,2.2,2.6,3. Blue/red: bid/ask densities; grey: relaxed initial field. Dotted placement quotes differ from dashed threshold quotes. Threshold 0.1; dx=0.025, du=0.00025; domain [-12.0125,12.0125]. Pre/post pairs preserve execution impulses. Display window [-8,8].

![Prices and market-maker state](figures/timeseries-v0.5.6.png)

**F3. Same-run prices and state.** Bid/ask/midpoint, actual fill-weighted execution log prices, observed spread and placement width, total/signed pending stock, cumulative execution/completion and placement centre. Placement uses old pending stock after delivery and before current execution. Completion is in volume units and does not generate another trade print.

![Balanced market-maker controls](figures/controls-v0.5.6.png)

**F4. Refined balanced controls.** Six alternating buy/sell children, volume 0.05 each. Compare both feedbacks, fixed placement and width only at dx=0.003125, du=0.00000390625. Initial placement edges lie on nodes (top) or between nodes (bottom), with matching axes. Responses subtract each stationary initial value; pending panels retain pre/post-event values. F2/F3 use their original coarser pilot grid. Time, space and matched fixed-control differences are in `control-comparisons`. Centre-only and the non-additive interaction remain at their prior resolution, retained in the data.

![Event-time paths and autocorrelations](figures/autocorrelations-v0.5.6.png)

**F5. Diagnostic paths and ACFs.** First 512 retained events of seed 41001; then true signs, midpoint increments, execution-log-price increments, their absolute increments and spread. Coloured curves average eight paths of 8192 retained events after 2048 burn events, comparing order splitting/moving, independent signs/moving and the same splitting tapes/fixed placement. Bands are descriptive mean ± two between-path standard errors. Dashed sign reference: exact finite-cap stationary renewal benchmark. Coloured curves use dx=0.05, du=0.001. Black midpoint/spread curves compare two matched full tapes at dx=0.025/0.0125, common du=0.0000625; they have no ensemble band. These remain diagnostic, not accepted limiting laws.

![Cross-correlations](figures/cross-correlations-v0.5.6.png)

**F6. Diagnostic cross-correlations.** Same paths and uncertainty convention. Spatial sensitivity remains unresolved. Positive lag means the first observable leads the second. Signed sign/spread-change and midpoint/spread-change correlations can cancel under buy/sell symmetry; magnitude/spread correlations address a different question. Correlation does not establish causality.

[![Video preview](figures/video-poster-v0.5.6.png)](figures/density-v0.5.6.mp4)

**V1. [24-second profile video](figures/density-v0.5.6.mp4).** F2/F3 trajectory, fixed axes and operational-time/phase labels. Stored states are held between frames; each execution has consecutive pre/post frames. No interpolation across impulses. Five PNG/PDF figure pairs and this video are the complete inventory.

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

The command runs 29 focused tests, 24 numerical assessment cases, 51 market-maker comparisons, 26 benchmark paths plus four common-step resolution paths, and the four main pilot/control trajectories, then produces all figures and the video. A repeat uses the same command. `python scripts/run_all.py --render-only` verifies the configuration/code/data hashes and redraws from saved states without solving. `python scripts/run_all.py --diagnose-only` verifies the saved inputs/data and exactly reproduces the bounded operator diagnosis and paper audit without evolving a path. `python scripts/run_all.py --refine-only` verifies saved inputs/data, repeats the six registered v0.5.4 finite refinement paths, and requires exact reproduction of the assessment arrays and comparison report. It preserves the inherited paths. `python scripts/run_all.py --controls-only` verifies saved inputs/data, independently repeats all 12 targeted control refinements and their comparison report, and requires exact output identity. The 39 inherited controls are preserved. A changed dynamical input requires the complete route. The tested runtime is Python 3.12.14, NumPy 2.3.5 and Matplotlib 3.10.8 on Linux; Windows execution remains unconfirmed. For this documentation stage, reuse saved arrays and use only `--diagnose-only` and `--render-only` in a separate validation copy. The accepted S5 numerical programme is not rerun. Executable/package versions and numerical filenames remain v0.5.6 to preserve their exact source/configuration/data manifest. Historical pending wording in retained runner messages and generated reports describes the pre-acceptance state; the current interpretation is stated here and in the v0.6.0 supplement.

## Configuration and retained data

`config/experiments-v0.5.6.json` is the sole active configuration. Parameters are dimensionless and illustrative: D=nu=1, kappa=0.5, Sigma0=12, chi_s=2, chi_m=0.5, completion time=1, outward placement width=0.5. Equal lit/latent amplitudes and lengths give constant total external supply outside placement edges. There is no empirical calibration.

| Directory | Active content |
|---|---|
| `config/` | One complete experiment configuration |
| `functions/` | Core, observations, finite driver, assessment, renderer |
| `scripts/` | One reproduction entry point |
| `tests/` | Three focused test files |
| `outputs/` | Fields, actual fills, paths, correlations, comparisons and hashes |
| `figures/` | F2–F6 PNG/PDF pairs; V1 MP4 and poster |
| `provenance/` | Algorithms, supplement, source identities and lineage audit |

The density archive retains incoming/pre/post fields, actual removals and source increments. Long paths retain all 10240 events, signs, distinct parents, lengths/ages, actual node fills and offsets; named columns identify the state matrices. `example-trades` contains the complete first moving-path tape with arithmetic and geometric execution prices. Correlation CSVs retain pair counts. Resolution paths retain source-membership changes and execution/field decomposition. Old generated versions remain in Git history and immutable checkpoints, outside the active file set.

The sign input is a stationary single-active-parent renewal benchmark with independent centred parent signs and capped integer lengths L=min(floor(2(1-U)^(-1/1.5)),512). The first parent is length-biased with uniform age. Child volume is 0.002 every 0.01 operational units; seeds 41001–41008. The exact sign reference is E[(L-k)+]/E[L]. It is not the full concurrent-parent LMF population, and no asymptotic exponent has been fitted or accepted.

## Accepted finite-grid result

Twelve targeted balanced controls cross dx=0.00625/0.003125 at common du=0.00000390625, both source phases and both/fixed/width-only feedback. Time comparisons use the retained dx=0.00625, du=0.000015625 runs; space comparisons hold the new step fixed. The six alternating 0.05 children and horizon 8 are unchanged.

| Comparison | Edge phase | Feedback | Absolute spread difference | Spread-response difference |
|---|---|---|---:|---:|
| Time | On nodes | Both | 0.00001458 | 0.00001458 |
| Space | On nodes | Both | 0.00519790 | 0.00439334 |
| Time | On nodes | Fixed | 0.00001462 | 0.00001462 |
| Space | On nodes | Fixed | 0.00519790 | 0.00207844 |
| Time | On nodes | Width only | 0.00001485 | 0.00001485 |
| Space | On nodes | Width only | 0.00519790 | 0.00439206 |
| Time | Between nodes | Both | 0.00001478 | 0.00001478 |
| Space | Between nodes | Both | 0.00238325 | 0.00237775 |
| Time | Between nodes | Fixed | 0.00001463 | 0.00001463 |
| Space | Between nodes | Fixed | 0.00207293 | 0.00207843 |
| Time | Between nodes | Width only | 0.00001486 | 0.00001486 |
| Space | Between nodes | Width only | 0.00273515 | 0.00272965 |

All new absolute-spread comparisons meet the unchanged 0.01 tolerance: **True**. Maximum baseline-subtracted spread-response difference is 0.00001486 for time and 0.00439334 for space. These are paired finite-grid comparisons, not a convergence order or continuum-limit proof. The response has no newly chosen acceptance tolerance. Both phases, including unfavourable results, are retained. Maxima use common 0.02 samples with post-event states at child times.

All 12 runs satisfy the registered execution, initialization, field-budget, completion-ledger and placement checks. Maximum budget/ledger errors are 3.63e-15/6.19e-15. Each programme fills gross volume 0.3 with unfilled volume below 1e-12. Matched effects against fixed placement and their spatial differences are retained. Centre-only and interaction results remain at v0.5.5 resolution. The long-path correlation ensemble is unchanged.

The retained finite-grid mechanism and these matched market-maker comparisons are sufficiently resolved for qualitative and bounded quantitative claims of this reproducibility study. All six successive spatial response differences decrease: on-node both, width-only and fixed change from 0.01075360, 0.01075331 and 0.00339765 to 0.00439334, 0.00439206 and 0.00207844; between-node values change from 0.00598659, 0.00619008 and 0.00347890 to 0.00237775, 0.00272965 and 0.00207843. This does not prove a continuum limit or convergence order. Acceptance concerns the density-defined quoted spread/midpoint at retained resolution, balanced-flow comparisons and the distinct roles of total-pending width and signed-pending centre feedback. Centre-only and interaction results retain their earlier resolution; no new precision is assigned to them.

## Remaining numerical and modelling limits

The inherited directional refinement passes the 0.01 absolute-spread comparison at both phases, but its on-node response differs by 0.01073. Half-cell padding preserves reflection while moving each reservoir by dx/2; separate domain checks are retained. Hard nodal supports and node-centre execution are unchanged, with no smoothing.

Two full-tape spatial refinements change midpoint and spread ACFs by up to 0.10340 and 0.12893. Fine-grid lag-one midpoint ACF is 0.636–0.651; whitening is not established. Trade-return statistics are less sensitive in those pairs, without a general convergence result. Frozen-operator diagnostics and a continuous execution-price reference separate some discretization effects; neither replaces the evolving solver. See the retained diagnosis and paper-audit outputs.

The fields aggregate order activity with an order-level DTRW interpretation. Static sources do not specify chartist/fundamentalist strategies, and the present mechanism tests require no additional agent population. Total and signed pending stocks differ even under balanced gross activity. Opposite-side replenishment is a completion-equivalent source closure, not an explicit second executed leg or a dealer profit calculation. Exact accounting does not establish financial equilibrium. Positive Sigma0 is imposed, so this pilot does not establish spread emergence from zero standoff. The diagnostic paths establish neither an asymptotic LMF/SQLR law nor universal volatility clustering. One programme size supplies no square-root-impact exponent. Systematic spread-dependent meta-order response and impact remains future v1.1.0.

## DTRW compatibility and paper provenance

The common Markov transport operator was checked against exact v2.0.0 source. The paper uses Euler cancellation while the prototype uses an exponential survivor; their finite-step difference and differing execution chronology are documented in the algorithm mapping. These are component checks, not whole-model equivalence. Execution prices and overlapping-pair Pearson ACFs follow the prior executable conventions.

Future Sibuya transport requires a history and a derived treatment of reaction, births and consumed volume. Keep it separate from sign memory, finite-mean completion and calendar subordination. No fractional transport or calendar clock is implemented. The supplement preserves the kernel, survival, scaling and completed-state observation conventions.

The prototype is [correlation-emergence v2.2.0](https://github.com/timgebbie/correlation-emergence-reproducibility/releases/tag/v2.2.0), with no runtime dependency. [Source provenance](provenance/SOURCES.md) connects the formulation to Diana–Gebbie CAM and Angstmann–Gebbie correlation emergence, and records exact manuscript/prototype identities. The current letter is SpreadLetter v1.2.0 by Christopher Angstmann, Derick Diana and Tim Gebbie; the supplied long paper remains v1.1.9. Neither manuscript is edited. Reaction price and quoted midpoint remain distinct; the distributed outward profile is not replaced by its narrow-placement limit. Private manuscripts and recovery administration remain outside the source tree.
