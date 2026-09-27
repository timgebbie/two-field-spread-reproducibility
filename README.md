# Two Field Spread Reproducibility

**v0.5.3 — paper-to-discretization audit and current letter alignment.** The requested density-derived figures and trade tape are implemented. Numerical convergence and scientific acceptance remain pending: midpoint and spread correlations are sensitive to resolution. The Markov DTRW core is unchanged from v0.4.1; no manuscript equation has been modified.

[Figures](#focused-numerical-outputs) · [Reproduce](#reproduce) · [Configuration](#configuration-and-retained-data) · [Assessment](#verification-and-current-limits) · [Market maker](#aggregate-agents-and-the-market-maker) · [DTRW lineage](#dtrw-compatibility)

The model evolves bid and ask densities in operational time through nearest-neighbour diffusion, cancellation and symmetric reaction. Actual aggressive executions initiate causal opposite-side replenishment. Pending exposure controls placement width and centre; inward density thresholds determine observed bid, ask, midpoint and spread. [Algorithm](provenance/ALGORITHM.md) and [supplement](provenance/supplement-v0.5.3.pdf) specify chronology, source geometry, execution and observation conventions.

## Focused numerical outputs

![Density evolution](figures/density-v0.5.3.png)

**F2. Density evolution.** Nine snapshots from six buys of volume 0.05 at u=1, 1.4, 1.8, 2.2, 2.6 and 3. Blue/red: bid/ask densities; grey: numerically relaxed initial field. Dotted placement quotes q differ from dashed threshold quotes p. The density threshold is 0.1. Pre/post pairs retain the execution impulse. Fixed display window [-8,8]; simulated domain [-12.0125,12.0125], dx=0.025, du=0.00025. Initial placement edges lie between grid nodes.

![Prices and market-maker state](figures/timeseries-v0.5.3.png)

**F3. Same-run time series.** Observed bid/ask/midpoint and actual fill-weighted execution log prices; observed spread and placement width; total and signed post-event pending stock; cumulative execution/completion; placement centre. Placement uses the residual old stock after delivery, before the current execution. The cumulative-flow panel is in volume units. Midpoint is the midpoint in log price.

![Matched market-maker controls](figures/controls-v0.5.3.png)

**F4. Market-maker controls.** One-sided and alternating buy/sell programmes have the same six absolute child volumes. Compare moving placement, next-update completion, both feedbacks off, width feedback off and centre feedback off. The displayed grid matches F2/F3. Responses subtract each case's initial stationary value; empty-pending reference dynamics coincide. Pending panels show post-event stock. The saved coarse/fine comparisons test sensitivity of the apparent feedback effect.

![Event-time paths and autocorrelations](figures/autocorrelations-v0.5.3.png)

**F5. Paths and ACFs.** Top: first 512 retained events of seed 41001. Lower panels: true signs, midpoint increments, execution-log-price increments, their absolute increments, and spread. Each coloured curve averages eight independent paths of 8192 retained events after 2048 burn events. Compare order splitting/moving placement, independent signs/moving placement, and the same splitting tapes/fixed placement. The dashed sign reference is the exact finite-cap stationary renewal benchmark. Bands are descriptive mean ± two between-path standard errors. The coloured curves use dx=0.05, du=0.001. In the midpoint and spread panels, the black dotted/dashed curves compare the same two full tapes at dx=0.025/0.0125, both with du=0.0000625; they have no ensemble uncertainty band. They are diagnostic figures, not accepted limiting laws.

![Cross-correlations](figures/cross-correlations-v0.5.3.png)

**F6. Cross-correlations.** Same benchmark paths and uncertainty convention as F5, with the two-path common-step refinements shown as black dotted/dashed curves. Positive lag means the first observable leads the second. Signed sign/spread-change and midpoint/spread-change correlations can cancel under buy/sell symmetry; magnitude/spread correlations address a different question. Correlation does not establish causality.

[![Video preview](figures/video-poster-v0.5.3.png)](figures/density-v0.5.3.mp4)

**V1. [24-second profile video](figures/density-v0.5.3.mp4).** The F2/F3 trajectory, fixed axes, operational-time/phase labels, spread and pending-stock cursors. Stored states are held between frames; children have consecutive pre/post frames. No interpolation across execution impulses. Five PNG/PDF figure pairs and one video constitute the focused inventory; no standalone theory gallery.

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

The command runs 28 focused tests, 18 numerical assessment cases, 23 market-maker comparisons, 26 benchmark paths plus four common-step resolution paths, and the four main pilot/control trajectories, then produces all figures and the video. A repeat uses the same command. `python scripts/run_all.py --render-only` verifies the configuration/code/data hashes and redraws from saved states without solving. `python scripts/run_all.py --diagnose-only` verifies the saved inputs/data and exactly reproduces the bounded operator diagnosis and paper audit without evolving a path. A changed dynamical input requires the complete route. The tested runtime is Python 3.12.14, NumPy 2.3.5 and Matplotlib 3.10.8 on Linux; Windows execution remains a later milestone.

## Configuration and retained data

`config/experiments-v0.5.3.json` is the sole active configuration. All parameters are dimensionless and illustrative. D=nu=1, kappa=0.5, Sigma0=12, chi_s=2, chi_m=0.5, completion time=1, placement width=0.5. Equal lit/latent amplitudes and lengths make total external supply constant outside placement edges. There is no empirical calibration.

| Directory | Active content |
|---|---|
| `config/` | One complete experiment configuration |
| `functions/` | Core, observations, finite experiment driver, focused assessment, renderer |
| `scripts/` | One reproduction entry point |
| `tests/` | Three focused test files |
| `outputs/` | Fields, actual fills and paths, correlations, budgets, comparisons and hashes |
| `figures/` | F2–F6 PNG/PDF pairs; V1 MP4 and poster |
| `provenance/` | Algorithm, supplement, source identities and the retained v0.4.1 lineage audit |

The density archive retains incoming/pre/post states, actual removal profiles and source increments. Long-path NPZ data retain all 10240 events per path, signs, distinct parent IDs, parent lengths/ages, actual node fills and offsets; `columns` names the state matrix. `example-trades` is the complete first moving-path CSV with observation conventions and arithmetic/geometric prices. Correlation CSVs include pair counts. The four `resolution-paths` retain the same state/fill records and named support columns: half-open intervals among interior node centres, external/completion membership flips during each event interval, and the number of field steps with a support change. `resolution-summary` separates common-grid time refinement from common-step spatial refinement. Budgets and admissibility are checked on every update, not just saved samples. Old generated versions remain in Git history and immutable checkpoints, outside the active file set.

The aggregate input has independent centred parent signs and capped integer lengths L=min(floor(2(1-U)^(-1/1.5)),512). Its first parent is length-biased with uniform age. New parents retain distinct IDs even when signs agree. Child volume is 0.002 every 0.01 operational units; seeds are 41001–41008, with a separate offset for the independent-sign null. The exact reference is E[(L-k)+]/E[L]. This is a single-active-parent renewal benchmark, not the full concurrent-parent LMF population. A fit window is reserved in the configuration, but no exponent has been fitted or accepted. Finite-cap data cannot establish asymptotic long memory.

## Verification and current limits

The 28 tests cover transport, reaction, budgets, positivity, causal completion, execution caps, threshold selection, reflection, initialization, trade measurements, lag alignment, the stationary parent-law/reference, source-support measurements restart invariance, frozen-state probes and the exact covariance decomposition, and continuous execution-reference moments. Main trajectories fill the requested 0.3; maximum field/ledger errors are below 3.2e-15/2.6e-15 and no-event drift below 9.5e-9. All registered assessment and statistical paths completed without material unfilled demand. Accounting consistency does not establish convergence.

The large late spread offset on the original node-aligned grid decreases with dx: approximately 0.1967, 0.0982, 0.0497, 0.0264 for dx=0.1, 0.05, 0.025, 0.0125. Placing the initial edges between nodes makes these offsets much smaller. This identifies a discretization effect; finite-horizon offsets are not permanent impact. Time-step/domain effects are much smaller in the tested pilot, and execution depths 1 and 4 give identical paths. No source smoothing was introduced.

The finest midpoint/spread comparison still fails the registered 0.01 spread tolerance: maximum spread differences are 0.02059 on-node and 0.01224 between-node. Long-path paired refinement changes midpoint-increment ACFs by up to 0.225 and spread ACFs by up to 0.193. F5/F6 therefore cannot yet support a physical claim about those statistics. Trade-price increment statistics are less sensitive in these two pairs, which is not a general convergence result.

The inherited v0.5.1 controlled comparison separates these effects. Maximum changes over the two matched paths and retained lags are:

| Refinement | Midpoint ACF | Spread ACF | Trade-return ACF | Any CCF |
|---|---:|---:|---:|---:|
| Time only, dx=0.025 | 0.00389 | 0.00547 | 0.000079 | 0.01130 |
| Space only, common du=0.0000625 | 0.10340 | 0.12893 | 0.000174 | 0.11826 |

Every retained child consumes one node at dx=0.025 and two at dx=0.0125. Source membership changes during about 11–12% versus 24–25% of retained event intervals. The midpoint execution-jump standard deviation falls from about 0.0182 to 0.0152; its partial cancellation with between-event field movement also changes. These observations identify spatial support/execution resolution as the principal remaining correlation sensitivity in this comparison; they do not isolate a single cause or establish convergence.

Time refinement still produces occasional spread differences up to 0.02461 (RMS about 0.0033–0.0034); spatial refinement produces differences up to 0.02144. Small ACF changes are therefore not a certificate of pathwise quote accuracy. At the finer grid, lag-one midpoint ACF is 0.636–0.651. The returns have not become white. Trade-return ACF is much less sensitive in these pairs, without establishing a general result.

Order-splitting sign persistence is present as a declared input. Mean lag-one midpoint-increment ACF is about 0.319; returns are not white in this run. Independent-sign trade returns show strong bid/ask bounce (about -0.496 at lag one). Absolute trade increments have an alternating short-lag pattern; no universal volatility-clustering or square-root-impact claim is made. Spread half-window means are retained for inspection, but stationarity and sampling adequacy are not scientifically accepted.

The paired resolution experiment holds both complete input tapes and physical child volume fixed. It compares dx=0.025 and 0.0125 at common du=0.0000625, with the existing dx=0.025, du=0.00025 paths as time-step controls. Each path retains 8192 events after 2048 burn events. Both source phases and the original spread tolerance remain in the finite assessment. The recorded midpoint increment is decomposed into its execution jump and evolution since the preceding trade; source-support changes are counted at every field update. Numerical interpretation must follow the resolution evidence.

The inherited v0.5.2 [operator diagnosis](outputs/diagnosis-v0.5.3.json) reuses these verified paths and the six saved pre-event density fields. No new trajectory or figure is introduced. On nested grids with identical endpoints, piecewise-linear resampling preserves every original density knot: pre-trade quotes agree within 2.7e-15. The unchanged execution rule nevertheless changes the post-trade spread jump by up to 0.01178 then 0.00663 for a 0.002 child as dx halves from 0.025 to 0.0125 to 0.00625. Actual execution-log-price differences are 0.00789 then 0.00392. These are frozen-operator differences, not finer evolved solutions. All six original executions replay exactly.

At fixed common placement quotes, the maximum external-source quadrature and completion-centroid errors in the phase sweep are approximately dx/2: 0.0125, 0.00625 and 0.003125. Completion normalization remains exact to roundoff. Crossing a source node gives a finite change in nodal supply even for a tiny quote displacement. The source reference integrates the same formula over retained interior cell intervals; it is never fed into the solver.

The lagged midpoint covariance decomposes exactly into execution/execution, execution/field, field/execution and field/field contributions. Large positive terms partly cancel negative cross-terms; their sum reproduces the ACF within 8e-16. They are signed normalized covariances, not causal shares or individually bounded correlations. Conditioning on source changes supplies no independent intervention. The diagnosis separates operator sensitivity from quote interpolation on a fixed representation, but cannot allocate full-path errors uniquely. DTRW equations, hard supports, quote definition and fill convention remain unchanged.

The current supporting letter is **SpreadLetter v1.2.0, Christopher Angstmann, Derick Diana and Tim Gebbie**. The long paper remains the supplied v1.1.9. The [paper-to-code audit](outputs/paper-audit-v0.5.3.json) retains their distinct input identities. The literal long-paper sources are evaluated at nodes with zero inward supply; cell averages assigned to those nodes would change that specification. No production source or execution replacement is justified by this audit.

An exact, continuous price-priority integral of each frozen piecewise-linear pre-event field supplies an execution-price reference only. For volume 0.002, maximum node-based price errors across the twelve side/event cases decrease from 0.01267 to 0.00556, 0.00263, 0.00146 and 0.00074 on successive grid halvings from dx=0.025 to 0.0015625. This supports refinement of the present rule; it is not convergence of evolving prices or spread. The reference generates neither a replacement field nor a trade tape.

The letter distinguishes the reaction price x_phi from the quoted midpoint. The saved finite-programme fields have three imbalance zeros immediately after each of the six executions; those frames are marked ambiguous rather than assigned an arbitrary reaction price. Among the uniquely resolved frames, the maximum difference from the quoted midpoint is 0.31847. The actual bid/ask threshold observations remain unchanged.

The pilot uses uniform outward replenishment of width w=0.5, with cancellation length ell_nu=1. Under the letter's frozen killed-diffusion approximation, its lag-integrated response is the point-at-edge response multiplied by `(ell_nu/w)*(1-exp(-w/ell_nu)) = 0.78694`. Thus the appropriate comparison is the distributed-profile convolution, not the narrow-placement point kernel. Density response, first passage and completion lag remain different quantities. No new figure or theory gallery is introduced.

## Aggregate agents and the market maker

The fields aggregate order activity with an order-level DTRW interpretation. Static source terms do not automatically specify chartist/fundamentalist strategies. No extra agent population is needed for the current mechanism tests.

Total exposure Q_A+Q_B drives width; signed inventory Q_A-Q_B drives centre. At the last child, directional and balanced programmes have the same total post-event pending stock, about 0.1379, while the balanced signed stock is about 0.0272 in magnitude. This makes the distinction visible. Centre-only response is unresolved: its balanced maximum midpoint effect is 0, 0.01494 and 0.00737 across the three grids. The zero on the coarse grid reflects unchanged nodal support and must not be interpreted as an absent centre mechanism.

Opposite-side replenishment is a **completion-equivalent source closure**, with probabilities assumed inside its delivery/placement law. It is not an explicit second trade or a profit calculation. All specified aggressor executions are attributed to the aggregate market-making sector. Reaction loss and completion do not create synthetic trade prints. Exact volume accounting does not establish financial equilibrium. The positive Sigma0 floor is imposed, so this pilot does not establish emergence from zero standoff. A systematic spread-dependent meta-order response/impact study remains scoped for future v1.1.0.

## DTRW compatibility

The common Markov transport operator was checked against exact v2.0.0 source. The current paper uses Euler cancellation; the prototype uses an exponential survivor. Their finite-step difference and execution chronology are documented in the [algorithm mapping](provenance/ALGORITHM.md). These are matched-component checks, not whole-trajectory equality. Price observations and overlapping-pair Pearson correlations follow the prior executable convention, with pair counts, explicit lag direction and undefined constant-series correlations.

Future Sibuya transport needs a transport history and a derived treatment of reaction, births and consumed volume. Keep it separate from order-sign memory, finite-mean completion and calendar subordination. No fractional transport or calendar clock is implemented. The supplement records the raw-kernel, survival, scaling and completed-state observation conventions to preserve.

The prototype is [correlation-emergence v2.2.0](https://github.com/timgebbie/correlation-emergence-reproducibility/releases/tag/v2.2.0). This clean implementation has no runtime dependency on it. [Source provenance](provenance/SOURCES.md) connects the spread formulation to Diana–Gebbie CAM and Angstmann–Gebbie correlation emergence, with exact manuscript/prototype identities. Manuscripts and recovery administration remain outside this source tree.
