# Source provenance

Reproducibility software for the forthcoming preprint **A Finite Bid–Ask Spread from Replenishment Displaced from the Quote**, by **Christopher Angstmann, Derick Diana and Tim Gebbie**.

- Accepted scaffold: `two-field-spread-reproducibility` v0.0.0, commit `53d85bfe2fbd6812ceb9195adac3b7b9e504d402`.
- Long paper: `TwoFieldSpread-v1.1.9`, original uploaded ZIP SHA-256 `9953b97aaf8b69f2539daa117051a1875042c8f6df7fd0da32578eda8fb2f893`.
- Historical letter: `SpreadLetter-v0.2.0`, original uploaded ZIP SHA-256 `a4fc11512b9b537f2de26e4027016edbe2d308a4c54843a935b6c63c42737e34`.
- Current letter: `SpreadLetter-v1.2.0`, supplied 27 September 2026; Christopher Angstmann, Derick Diana and Tim Gebbie, in that order. Original ZIP SHA-256 `576a690f2a3cf5b5e87c462dbd19cdad8af96c4afa85e7f592311bf278077322`. Both the supplied TeX and five-page PDF carry these authors.
- Accepted implementation-design specification: v0.1.0; source-shape, slope/capacity and threshold-branch qualifications are carried into this version.
- Numerical/presentation prototype: [correlation-emergence v2.2.0](https://github.com/timgebbie/correlation-emergence-reproducibility/releases/tag/v2.2.0), commit `70e88f7157a4a18e63a4e407be9eae05f8667f9c`.
- Algorithm/measurement antecedent: [correlation-emergence v2.0.0](https://github.com/timgebbie/correlation-emergence-reproducibility/releases/tag/v2.0.0), commit `3107bacecb407f2b90c13c5f9f1c52136aa0184c`.

This is a clean, thinned implementation. The numerical core and tests were independently written; no prototype production module is imported or copied. The prototype Figure 12/13 square-panel presentation is used for the numerical snapshots and time series. Its release/configuration controls informed input hashing, pinned dependencies and one reproduction entry point. Its multi-version configuration archive, clock experiments and release-governance modules are not imported. Standalone theory illustrations from v0.2.0 were removed from the active project. Future code adaptation must identify the source component and preserve its applicable license notice. The prototype's two-book dynamics are not identified with bid/ask side densities.

The original manuscript ZIPs, private design decisions and disaster-recovery records are retained outside the source repository. This source tree records their identities without redistributing the manuscripts. No numerical calibration or empirical-data source is used.

The v0.4.0 audit checked the discrete parent, positivity condition, source support, event-integrated cap, completion/placement definitions and side-level quotes against the long paper. One code diagnostic was corrected to the explicit sup/inf crossing convention. No error in the manuscript formulation was established and neither manuscript was edited. No claim of a new equation or universal numerical law is made.

## v0.4.1 lineage inspection

The following exact v2.0.0 components were inspected at the commit above. SHA-256 values identify retrieved bytes, not current runtime dependencies.

| Component | SHA-256 | Use |
|---|---|---|
| `functions/operational/memory.py` | `2047fd145e7a3b49c3907cc3dfcaab55d3f9e82e5c80e04992b3ca0c3db97578` | Raw Sibuya kernel, one survival factor and matched Markov operator audit |
| `functions/events/records.py` | `241db8eb95854d8498538cafdac1eb7a0342faf0989ea728478de2e89191bdb2` | Fill-volume-weighted execution log price and separate aggressor/quote/tick signs |
| `functions/events/tape.py` | `ff94fdc3bfda634f133e426bfb8781b44a723afaa1d910ac10f622cdf3c1040d` | Event-before-field chronology comparison |
| `functions/path_diagnostics.py` | `c71b83de103743000855ff25768c8ba0c18e718b12133fef0660ef620ca508de` | Overlapping-pair Pearson ACF |
| `functions/observation/refresh_sampling.py` | `79161984d9aed19e694957b64817939b7e891ada793331c8eff1467813049e6b` | Previous-completed-state observation and paired clock design |
| `SUPPLEMENTARY-MATERIAL-v2.0.0.tex` | `960400980ae7224eca072f71ec9e69ead8bc0c9cc11024a4d48a66d55f403bf4` | Algorithm presentation; ACF text/code mismatch documented |

The v2.2.0 tape, path-diagnostic and refresh-sampling files are byte-identical to those v2.0.0 components. Its numerical algorithms, renewal clocks and Pareto-run configuration were also inspected. The earlier finite-persistence sign fixture is not relabelled as LMF. The new observable implementation was written independently to the documented measurement convention and compared against the executable estimator. No prototype production module is shipped as a runtime dependency.

The matched reaction-free, cancellation-free interior operator agrees within 2.3e-16; positive-cancellation differences equal the derived survivor difference within 3.4e-16. The new ACF agrees with the prior executable ACF within 1.2e-16 on the registered nondegenerate comparison. These checks do not establish whole-model equivalence or fractional two-side correctness. That v0.4.1 audit left the core and numerical trajectories unchanged from v0.4.0. In v0.5.4, `core.py` is still byte-identical (SHA-256 `b8c4a1349b51d730fb44f0afbdf73f5e776e0376315f0d29bc5bb12a4f853315`); v0.5.4 adds six finer finite-programme trajectories using that core. The compatibility JSON is retained as a historical component audit, not a v0.5.4 convergence certificate.

## Literature crosswalk

- [Diana and Gebbie, CAM](https://doi.org/10.1016/j.cam.2024.116202): *Non-uniformly sampled simulated price impact of an order-book*, Journal of Computational and Applied Mathematics 456 (2025), 116202; [author manuscript](https://arxiv.org/abs/2310.06079). This establishes the DTRW order-book antecedent and explicitly notes the need for separate densities for nonzero spread. Its earlier nonuniform stepping is not silently substituted for the later fixed-operational-grid/observation-clock construction.
- [Angstmann and Gebbie, correlation emergence](https://arxiv.org/abs/2606.14182), v3: operational DTRW and a distinct calendar observation layer. The present project extends the representation to the sides of one book and its market-maker pending state.
- [Angstmann and Gebbie, event-time order-flow memory and operational-time impact](https://arxiv.org/abs/2609.13715): the abstract explicitly separates sign memory, impact and observation clocks. This is contextual support, not a full-text formulation audit. The supplied paper cites the earlier `2606.16269` companion and already flags its citation identity for author confirmation; neither manuscript citation is silently replaced.
- [Lillo, Mike and Farmer](https://arxiv.org/abs/cond-mat/0412708): persistent signs from order splitting with heavy-tailed parent sizes. This supplies a conditional order-flow benchmark, not a result already demonstrated by the current simulation.
- [Donier et al.](https://arxiv.org/abs/1412.0141): reduced reaction-diffusion impact limits. A future scaling comparison must establish its applicable regime; it is not guaranteed by sharing a DTRW lineage.

The uploaded long-paper bibliography has mixed CAM title/year/volume metadata; this supplement uses the publisher DOI metadata above. The uploaded manuscripts remain byte-for-byte unchanged. The new draft is an algorithm specification and experiment design, not scientific acceptance of numerical agreement with their limiting analysis.

## Retained numerical lineage and current audit

v0.5.1 added four full common-step paths to the v0.5.0 numerical assessment and repaired the incomplete F5 PDF. v0.5.2 added the frozen-operator and covariance diagnostics. These stages are not relabelled as newly computed v0.5.4 trajectories. At v0.5.4, their six non-assessment NPZ archives and 17 CSV tapes remained byte-identical under the active versioned names. The assessment archive retains every inherited array exactly and adds six v0.5.4 refinements. Prior full numerical recovery evidence applies to those unchanged arrays.

v0.5.3 checked the literal nodal source support, normalization, forcing cap and threshold interpolation against long-paper v1.1.9. The production core remains unchanged. A cell-average source assigned to node centres is rejected as an unchanged implementation of the discrete equations. Continuous integration is used only as a frozen execution-price reference. The retained paper-audit JSON records reference errors, source-support counterexample, reaction-zero multiplicity and the distributed-placement response benchmark.

The current letter clarifies one-field threshold width versus an independent placement scale; branch-specific supply withholding; reaction price versus quoted midpoint; distributed versus narrow placement; density-response versus first-passage kernels; and finite-window capacity. Its new figure's dotted latent-book reference is not an additive density or an external source. These distinctions inform the implementation and supplement; the schematic is not added to the simulation figure inventory.

The current letter's sentence immediately after the field decomposition should distinguish two facts: symmetric reaction cancels algebraically from the imbalance equation even with unequal D or nu; equal coefficients remove the transport/cancellation coupling to total density. This is a wording issue, not a reason to alter the implemented equal-coefficient recurrence. The supplied manuscripts are preserved unchanged. Long-paper authorship is recorded as supplied and is not silently changed to match the new letter.

F2–F6 and V1 remain the entire output inventory. No strategic agent, new source law, transport memory or calendar clock is introduced. The PDF writer now stages complete bytes in a temporary directory with automatic cleanup; that repair changes no numerical result. Private manuscript ZIPs and recovery administration stay outside the scientific source tree.

The v0.5.4 six-run matrix uses dx=0.0125/0.00625 at common du=0.000015625 and halves du on the finer grid to 0.0000078125, for source phases 0 and 0.5. The existing dx=0.0125, du=0.0000625 paths supply additional time controls. Each uses the same six 0.05 buys and physical threshold 0.1, ending at u=8. The unchanged finite runner relaxes each field independently to rate-residual tolerance 1e-8. Comparisons use the common 0.02 output times including all six event times. They do not certify the maximum between saved samples. No long path, market-maker control or display trajectory is replaced by these refinements.

## v0.5.5 control refinement

Sixteen registered balanced controls use unchanged `finite_run`, `grid_model`, `long_run` and `core.py`. All inherited scientific configuration values remain unchanged; worker count only changes scheduling. The 23 inherited market-maker arrays and summaries are retained exactly. Six unaffected numerical archives and 17 CSV tapes retain v0.5.4 bytes. F4 now displays refined balanced controls; the other figure/video trajectories remain unchanged. The sole new output family is the control comparison JSON, within the existing outputs directory.

The supplement corrects a reversed verbal description: aggressive buys consume ask liquidity and initiate bid replenishment Q_B; aggressive sells consume bid liquidity and initiate ask replenishment Q_A. This agrees with long-paper equations `eq:pendingBid`, `eq:pendingAsk` and the existing `actual[::-1]` initiation in `core.py`. No code recurrence or manuscript equation is changed.

## v0.5.6 response refinement

Twelve targeted controls refine time and space with the same production worker and source geometry. All 39 inherited control arrays and numerical summaries remain exact. The six unaffected NPZ archives and 17 CSV tapes are byte-identical to v0.5.5 under the active versioned names. F4 displays the finer grid with both/fixed/width-only settings; centre-only and interaction comparisons remain retained at their previous resolution. No mathematical formulation, long ensemble, agent, memory law or clock is added.

## v0.6.0 documentation and accepted interpretation

The scientific parent is v0.5.6, commit `47bc56d20b03e6c90d33ca9727902ff0d33017cf`. Its numerical source/configuration, arrays, diagnostic reports, figure/video bytes and original manuscript identities are retained unchanged. Numerical filenames and executable/package versions remain v0.5.6; v0.6.0 identifies the consolidated README, algorithm qualifications and supplement. Historical pending wording in immutable generated reports is not rewritten.

The finite-grid two-density mechanism and matched market-maker comparisons are accepted for qualitative and bounded quantitative claims at the retained resolution. All new absolute-spread comparisons meet the unchanged 0.01 tolerance; no response tolerance is introduced. All six successive spatial response differences decrease, without establishing continuum limit or convergence order. F2/F3/F4/V1 retain their existing limits. Centre-only/interaction remain at v0.5.5 resolution. F5/F6 remain diagnostic with unresolved spatial sensitivity. No model, equation, tolerance, agent, source smoothing, transport memory or clock is changed. Private acceptance and recovery records remain outside this scientific tree.
