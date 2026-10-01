# Numerical algorithm v0.5.6

[Compiled supplementary algorithms](supplement-v0.5.6.pdf) ([LaTeX source](supplement-v0.5.6.tex)) describe the implemented field update, execution tape, stationary renewal input and diagnostic correlations. The core equations and core source are unchanged from v0.4.1; grids and experiment inputs are explicit in the current configuration. Scientific acceptance and future memory/clock extensions remain pending.

Rows are bid then ask. The uniform coordinate is log price x; du is operational time per numerical update. Interior density values represent volume per log-price and each carries quadrature weight dx. Endpoint values are fixed reservoirs and are excluded from the interior standing-volume sum.

## One update

1. Start with the previous post-consumption densities and post-execution pending stocks P_B, P_A.
2. Allocate due completion C=(1-exp(-du/tau_h)) P. For the immediate control, C=P. Residual Q=P-C is the stock used to set this update's placement quotes. It excludes the current event.
3. Set Sigma=Sigma0+chi_s(Q_A+Q_B), mu=mu0-chi_m(Q_A-Q_B), q_b=mu-Sigma/2 and q_a=mu+Sigma/2.
4. Evaluate nonnegative lit and latent sources outside q. Normalize outward uniform nodal placement weights so dx sum(g)=1; the whole support must be inside the retained interior grid. Add C_i g_i as a density increment, without another factor du.
5. From a single frozen two-side state, apply nearest-neighbour diffusion, explicit cancellation, symmetric reaction and external supply times du. Verify the sufficient bound 2D du/dx^2 + nu du + kappa du rho_opposite <= 1 everywhere. Reject an unsafe registered step.
6. Read pre-consumption threshold quotes. A sell consumes bid nodes from highest eligible price downward; a buy consumes ask nodes from lowest eligible price upward. Only interior node centres between the observed quote and the configured outward execution depth are eligible. Each node supplies at most rho_j dx. Save actual removal and unfilled demand. Both side impulses act on the same pre-consumption field, and do not interact through a second reaction step.
7. Add actual buy volume to pending bid completion and actual sell volume to pending ask completion. New executions cannot complete in this update. Read the post-consumption quotes and save both quote-setting and post-execution stocks.

An event configured at u is applied at the endpoint of the numerical interval ending at u. The first admissible event time is du. The incoming state has timestamp u-du; pre- and post-consumption states have the endpoint timestamp u and different phase labels. q is the placement used throughout that update. This follows the accepted algebraic timing convention; it does not label Q as every possible post-trade inventory sample.

## Standing-volume and completion budgets

For side i, each completed update obeys

`change = boundary_flux - cancellation - matched_reaction + external_supply + completion - actual_execution`.

The diffusion flux increment is `D du/dx * (rho_0-rho_1+rho_J-rho_(J-1))`. Matched reaction is `kappa du dx sum(rho_A rho_B)` and is removed once from each side. Thus it cancels from imbalance and contributes twice to total-density loss. Fixed reservoirs are not executable volume.

For each receiving side, cumulative actual initiation equals cumulative completed supply plus post-execution pending stock. A buy initiation has negative signed inventory Q_A-Q_B. The immediate control means completion at the next permitted update, not the same event. Geometric weights are recomputed from fixed operational tau_h when du changes.

No density projection is used. Fully consumed cells are set to exactly zero as the execution cap; only a possible floating-summation residual in unfilled demand is rounded to zero. The ledger and field budgets are checked separately.

## Observations and source geometry

Quotes are linearly interpolated, correctly oriented inward threshold crossings. Select the rightmost bid downward crossing and leftmost ask upward crossing: the paper's supremum/infimum convention, including when there are other crossings. Record crossing counts. A plateau adjoining the selected crossing, an insufficient selected slope, reservoir failure or unresolved/nonpositive spread causes an explicit exit. This corrects the v0.3.0 blanket rejection of multiple crossings; it does not alter either field equation. A machine-roundoff contact guard is 32 epsilon_machine times the larger of one and the domain width; it is not a physical contact threshold.

Lit/latent sources use the paper's one-sided exponentials and support indicators. Their amplitudes and lengths are equal in this registered pilot, yielding a constant total source outside q. The uniform completion profile uses only centres in [q_b-w,q_b] or [q_a,q_a+w], with boundary weights zero. Its actual grid centroid and standard deviation are saved. Nodal hard support and node-centre execution introduce resolution effects; their refinement is required before final comparisons. The algorithm never renormalizes a source whose intended support is cut by a reservoir.

## Initialization and retained data

Explicitly relax the same positive-reaction field equations with empty pending stock and no executions until max(abs(next-current))/du is below the registered stationarity tolerance. Keep reservoirs fixed. Save the achieved residual and duration; the tolerance concerns the numerical reference, not a theorem about the continuum model.

The experiment has six buy children of volume 0.05 at u=1, 1.4, 1.8, 2.2, 2.6 and 3, followed to u=8. All three event cases start from the same stationary field. Compare delayed/moving placement, next-update completion, and delayed/fixed placement. Their empty-pending no-event equations are identical, so one no-event trajectory suffices. Actual child volumes must agree within the registered tolerance; unfilled demand is not hidden.

Scalar states are saved every 0.01 operational units, at every child and at its neighbouring updates. Budget, positivity and quote checks run at every numerical update. Density states are saved every 0.025 units and at requested snapshots, with both pre/post views at every child. Event arrays additionally retain incoming densities, removals, completion and separate lit/latent increments. The video holds stored density states without interpolating them and assigns consecutive pre/post frames to each child. Its frame index gives the actual operational time and phase, independently of video time.

The inherited 18-case assessment varies dx, du, domain, source/grid phase, threshold and execution depth. Symmetric half-cell padding puts initial source edges between nodes while preserving buy/sell reflection; separate domain tests bound the reservoir shift. Both tested phases fail the inherited dx=0.025/0.0125 spread comparison tolerance. Hard supports and node-centre execution are retained without smoothing. Finite-grid late offsets are not permanent impact.

## Equation and prototype mapping

Paper: TwoFieldSpread v1.1.9, `eq:bid`, `eq:ask`, `eq:positivityStep`, `eq:litBid`–`eq:latentAsk`, `eq:mmB`, `eq:mmA`, `eq:pendingBid`, `eq:pendingAsk`, `eq:placementSpreadLaw`, `eq:placementCentreLaw`, `eq:placementWeights`, `eq:placementSupportQuote`, `eq:forcingCap` and the side-level quote definitions.

The code uses the audited explicit cancellation and pre-consumption source order. The v2.0.0/v2.2.0 prototype's exponential survivor, two-book imbalance interpretation and event ordering are not asserted identical. With reaction off, map the transport probability by r=2D du/dx^2. The matched interior operator agrees to roundoff at nu=0. At positive nu, prior-minus-current is (exp(-nu du)-1+nu du)rho, a one-step O(du^2) difference. The prior code consumes before advancing the field; this implementation consumes afterwards. Boundary/source geometry also differs. [Executed compatibility checks](compatibility-v0.4.1.json) record the exact comparison scope.

## Trade prices and statistical observations

`functions/observables.py` calculates execution log price from actual node fills as sum(v_j x_j)/sum(v_j), following the prior v2.0.0 executable convention. It stores exp(mean log price) separately from arithmetic price VWAP. Fill rows, actual aggressor signs, parent identifiers, phase-labelled quotes, placement state, both pending samples, unfilled demand and tick/quote sign classifications are retained. First consecutive-trade increments are missing rather than zero. The finite six-child programme belongs to parent 0; the stationary renewal generator supplies distinct parent IDs to the long two-sign tapes.

Only explicit nonzero aggressor executions create trade observations. Symmetric reaction is a field sink without a reconstructed trade tape. Completion-equivalent source delivery creates no trade print. All executed programme volume is assigned to the aggregate market-making sector in this pilot; this is an attribution assumption, not inference of individual counterparties.

The implemented lag estimator is Pearson Corr(X_n,Y_(n+k)), with separate centring of the overlapping slices, as in the v2.0.0 executable `increment_autocorrelation`. Its supplementary text prints a different global-mean normalization; the new supplement follows and verifies the code convention. Positive lag means X leads Y. Missing alignment and zero-variance slices are rejected rather than silently compressed or zero-filled. Six all-buy events cannot identify a sign ACF.

## Implemented assessment and interpretation

Market-maker comparisons cross one-sided and alternating flow with moving placement, next-update completion, both feedbacks off, width feedback off and centre feedback off. Coarse/primary grids run all ten combinations; three fine balanced cases isolate centre sensitivity. Filled absolute volume is matched. Total pending stock persists under balanced flow with much smaller signed stock. Centre effects change with grid spacing and are not accepted as resolved.

For the long paths, draw L=min(floor(2(1-U)^(-1/1.5)),512), independent centred parent signs, and a length-biased first parent with uniform age. Same-sign neighbours keep different parent IDs. The reference C(k)=E[(L-k)+]/E[L] is for this stationary single-active-parent renewal law. It is an aggregate order-flow closure with an LMF-type tail, not endogenous RD sign memory or the full concurrent-parent model. Run eight seeds for moving splitting, independent signs and fixed-placement splitting; pair the first two splitting seeds on a finer grid. Each path has 2048 burn and 8192 retained events, volume 0.002, spacing 0.01. The first retained increment uses the preceding burn-event price. Record all actual fills and inadmissible exits; all current paths completed.

F5/F6 use pathwise Pearson ACFs and CCFs over lags up to 128, then average independent paths. Bands are descriptive mean plus/minus twice the between-path standard error, not iid-event confidence bands or a hypothesis test. Matched-control paths are paired, not extra independent replicates. Store per-path correlations, pair counts, spread half-window means and grid comparisons. No exponent fit or stationarity acceptance has been made. Midpoint and spread statistics remain materially sensitive to dx/du; their plotted differences cannot yet be interpreted as physical effects.

Static source terms do not automatically encode individual chartist/fundamentalist strategies. No additional agent population is required. Completion-equivalent supply is not a second executed leg; its exact volume ledger establishes no profit equilibrium. Positive Sigma0 is imposed. Fixed mu0 and reservoirs can anchor prices; neither white returns, volatility clustering nor square-root impact is enforced. A systematic spread/meta-order impact study remains a later extension. F2–F6 and V1 remain the entire focused figure inventory.

## Future Sibuya and observation contract

Keep order-splitting memory, operational Sibuya transport, finite-mean round-trip completion, and calendar subordination separate. Preserve the prototype's raw kernel, single elapsed-time survival weighting, lag indexing, transport scaling and previous-completed-state observation convention. The current core has no transport history and no calendar clock. A nonlinear two-side fractional extension requires a stated treatment of reaction, births and removal in the history; it must not resurrect consumed volume. An infinite-mean completion law would violate the stationary placement assumptions even when Sibuya transport is appropriate. These are design constraints, not a claim of implemented plug-in compatibility.

## Paired resolution measurements

The same two complete renewal tapes are run at dx=0.025 and 0.0125, both with du=0.0000625. Physical child volume, event spacing, burn-in and retained event count are fixed. The stored dx=0.025, du=0.00025 paths provide the separate time-step comparison. These long paths use symmetric half-cell padding; both source phases remain in the finite assessment.

For each executed event n, let m_n^- and m_n^+ be the pre- and post-consumption threshold midpoints. The exact decomposition is

`m_n^+ - m_(n-1)^+ = (m_n^+ - m_n^-) + (m_n^- - m_(n-1)^+)`.

The first component measures the execution jump; the second measures the field evolution since the preceding event. Actual fill counts come from recorded removed node volumes. At every field update, the external and completion support intervals are compared with those used on the preceding update. Count the nodes entering or leaving each support, including repeated changes within an event interval; event-level snapshots alone would miss those changes. These diagnostics do not alter the state update. Event-indexed ACFs and CCFs use the same estimator and lags as the benchmark.

## Frozen-operator diagnosis

The inherited v0.5.2 diagnosis is a read-only calculation from verified saved fields and paths. It does not generate an alternate trade tape. For each of six pre-event density fields, subdivide each original interval into 1, 2 or 4 intervals, keeping endpoints and every original piecewise-linear knot. Read the unchanged threshold quotes, then independently execute buy and sell probes of volume 0.002 and 0.05 using the unchanged price-priority cap. Discard each probe state. Record pre/post quotes, fill indices/quantities, fill-weighted log price and mass residual. The base-grid historical requests reproduce saved removals and post-fields exactly. Agreement of pre-quotes tests interpolation on this fixed representation, not convergence of evolving threshold level sets.

Separately, translate common placement quotes across one original cell with 129 equally spaced shifts. On each nested grid compare the nodal external volume with the exact integral of the same lit/latent formula over the retained interior cells. Compare the normalized uniform completion centroid with q_b-w/2 and q_a+w/2. Probe a source-node crossing on either side by epsilon=dx*1e-8. These reference integrals and centroids do not alter the source evaluated by the solver. Completion normalization and source approximation accuracy are distinct checks.

For the recorded long-path increments J_n=m_n^+-m_n^- and F_n=m_n^--m_(n-1)^+, decompose the overlapping-pair Pearson numerator into Cov(J,J'), Cov(J,F'), Cov(F,J'), Cov(F,F'). Divide every term by the same sd(J+F) sd(J'+F'), with slice-specific centring at each lag. The sum is the total midpoint-increment ACF; individual terms may exceed one or be negative. Source-change conditional averages are descriptive only: support changes, order flow and inventory are dependent. No fraction is labelled a causal contribution. The fixed-field and source probes do not establish whole-trajectory convergence or an alternative mathematical model.

## Paper-to-discretization audit and current letter

The long paper v1.1.9 specifies pointwise nodal lit/latent formulas (`eq:litBid`–`eq:latentAsk`) and forbids receiving-side placement nodes inside the placement interval (`eq:placementSupportQuote`). Nonnegativity and unit total completion mass (`eq:placementWeights`) hold separately from source accuracy. A cell-average source attached to an inward node changes the literal discrete support even when its underlying continuum integration interval is correct. Such a finite-volume representation needs an explicit state and support interpretation; it is not applied here. The existing forcing cap and quote interpolation agree with `eq:forcingCap` and `eq:discreteBidCrossing`.

For the execution reference, integrate each frozen piecewise-linear side profile outward from its observed pre-trade quote. In a segment of length h with density a+b z, the consumed volume is a h+b h^2/2 and the local first moment is a h^2/2+b h^3/3. Solve the final partial-segment volume equation, stop at the same outward execution depth, and report any unfilled demand. Divide the summed log-price moment by actual reference volume. No field is updated and no reference price enters the simulated trade tape. The five nested grids retain every original density knot and fixed endpoints.

The current letter v1.2.0 is by Christopher Angstmann, Derick Diana and Tim Gebbie. Its reaction price is a zero of phi, distinct from the quoted midpoint. Record a reaction price only where the sampled piecewise-linear imbalance has one zero; mark multiple zeros or a zero interval ambiguous. Impulsive depletion creates three zeros in the six stored immediate post-execution fields. No selection convention is invented.

For a frozen uniform receiving profile over outward distance z in [0,w], the killed-diffusion lag-integrated response relative to a same-location point is exp(-d/ell_nu)*(ell_nu/w)*(1-exp(-w/ell_nu)). This follows by averaging exp(-(d+z)/ell_nu) over the actual profile. The point-at-edge approximation requires w/ell_nu small; the current value is 0.5. This is a reference calculation under the letter's stated approximation, not validation of the nonlinear solver. Its density kernel is not a first-passage density, and neither kernel is the assumed completion law. No instantaneous local capacity is inserted into the update.

## v0.5.4 matched finite refinement

Append six runs to the existing assessment: for each source phase 0 and 0.5, use dx=0.0125 and 0.00625 at common du=0.000015625; halve du to 0.0000078125 at dx=0.00625. Reuse older dx=0.0125, du=0.0000625 trajectories only as time controls. Each run independently relaxes its grid to the same rate-residual tolerance, then applies the unchanged six-child programme through u=8. Physical thresholds, child volumes, placement supports, source values and event chronology remain fixed. The finest-grid diffusion contribution to the positivity load is 0.8 before time halving and 0.4 afterwards; the full load is checked on every production update.

Retain common 0.02 output times including every event time, final fields, initial residuals, executed/unfilled totals, and field/ledger error maxima. Compare maximum absolute midpoint/spread differences and initial-value-subtracted responses on common samples. The original 0.01 absolute spread tolerance is unchanged. It is not a normalized response tolerance, an every-update bound or a long-path correlation acceptance criterion. Keep historical and new comparisons together, distinguishing finest spatial from finest temporal checks. The saved-data refinement route verifies input/data hashes before and after repeating the six runs.

## v0.5.5 matched balanced-flow feedback assessment

Six alternating children retain the same actual volumes, times and completion law. Cross dx=0.0125/0.00625 at common du=0.000015625, phases 0/0.5 and four settings: both feedbacks; fixed; centre only (chi_s=0); width only (chi_m=0). Each grid initializes independently.

For midpoint or spread y, retain R_mode(u)=y_mode(u)-y_mode(0) and E_mode(u)=R_mode(u)-R_fixed(u). Compare absolute values, responses and matched effects at identical times across grids. Retain the non-additive interaction R_both-R_width-R_centre+R_fixed; it is not an allocation to causal shares. The existing 0.01 tolerance applies to absolute spread; response differences are reported without a new outcome-selected acceptance threshold.

Check actual volume, field/ledger budgets, equal pending schedules and the placement formulas. Accounting is checked every update; response comparisons use common 0.02 output times with post-event states at every child. The inherited directional time tests do not certify balanced-control time convergence. F4 displays both source phases at the finer grid.

## v0.5.6 targeted time and spatial checks

Cross dx=0.00625/0.003125 at common du=0.00000390625, phases 0/0.5 and both/fixed/width-only feedback (12 cases). At dx=0.00625 compare against the retained du=0.000015625 run. Hold every physical event and model parameter fixed. Apply the same absolute, baseline-subtracted and fixed-control response comparisons above. Centre-only and nonlinear interaction are not recomputed at this finer grid. No response tolerance or convergence order is inferred from the two spacings.
