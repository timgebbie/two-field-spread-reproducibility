# Numerical algorithm v0.4.0

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

The mesh pilot changes only dx and du, from (0.1,0.002) to (0.05,0.001), retaining physical thresholds, completion time, source width, programme and domain. It diagnoses sensitivity; it is not a convergence proof. In particular, sources are evaluated at nodes with hard indicators. The initial placement edges lie on nodes. Any small outward displacement excludes those edge nodes, even during late recovery with a small positive pending stock. The resulting finite-grid spread offset must not be interpreted as permanent impact or an additional model mechanism. v0.5.0 must check mesh phase as well as grid, time step, domain and event resolution.

## Equation and prototype mapping

Paper: TwoFieldSpread v1.1.9, `eq:bid`, `eq:ask`, `eq:positivityStep`, `eq:litBid`–`eq:latentAsk`, `eq:mmB`, `eq:mmA`, `eq:pendingBid`, `eq:pendingAsk`, `eq:placementSpreadLaw`, `eq:placementCentreLaw`, `eq:placementWeights`, `eq:placementSupportQuote`, `eq:forcingCap` and the side-level quote definitions.

The code uses the audited explicit cancellation and pre-consumption source order. The v2.2.0 prototype's exponential survivor, two-book imbalance interpretation and event ordering are not asserted identical. The present core is independently implemented. The supplementary algorithm will be drawn from this actual implementation after numerical assessment.
