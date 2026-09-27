# Source provenance v0.5.1

- Accepted scaffold: `two-field-spread-reproducibility` v0.0.0, commit `53d85bfe2fbd6812ceb9195adac3b7b9e504d402`.
- Long paper: `TwoFieldSpread-v1.1.9`, original uploaded ZIP SHA-256 `9953b97aaf8b69f2539daa117051a1875042c8f6df7fd0da32578eda8fb2f893`.
- Pinned letter: `SpreadLetter-v0.2.0`, original uploaded ZIP SHA-256 `a4fc11512b9b537f2de26e4027016edbe2d308a4c54843a935b6c63c42737e34`.
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

The matched reaction-free, cancellation-free interior operator agrees within 2.3e-16; positive-cancellation differences equal the derived survivor difference within 3.4e-16. The new ACF agrees with the prior executable ACF within 1.2e-16 on the registered nondegenerate comparison. These checks do not establish whole-model equivalence or fractional two-side correctness. That v0.4.1 audit left the core and numerical trajectories unchanged from v0.4.0. In v0.5.1, `core.py` is still byte-identical (SHA-256 `b8c4a1349b51d730fb44f0afbdf73f5e776e0376315f0d29bc5bb12a4f853315`); new grids and registered inputs produce new trajectories. The compatibility JSON is retained as a historical component audit, not a v0.5.1 convergence certificate.

## Literature crosswalk

- [Diana and Gebbie, CAM](https://doi.org/10.1016/j.cam.2024.116202): *Non-uniformly sampled simulated price impact of an order-book*, Journal of Computational and Applied Mathematics 456 (2025), 116202; [author manuscript](https://arxiv.org/abs/2310.06079). This establishes the DTRW order-book antecedent and explicitly notes the need for separate densities for nonzero spread. Its earlier nonuniform stepping is not silently substituted for the later fixed-operational-grid/observation-clock construction.
- [Angstmann and Gebbie, correlation emergence](https://arxiv.org/abs/2606.14182), v3: operational DTRW and a distinct calendar observation layer. The present project extends the representation to the sides of one book and its market-maker pending state.
- [Angstmann and Gebbie, event-time order-flow memory and operational-time impact](https://arxiv.org/abs/2609.13715): the abstract explicitly separates sign memory, impact and observation clocks. This is contextual support, not a full-text formulation audit. The supplied paper cites the earlier `2606.16269` companion and already flags its citation identity for author confirmation; neither manuscript citation is silently replaced.
- [Lillo, Mike and Farmer](https://arxiv.org/abs/cond-mat/0412708): persistent signs from order splitting with heavy-tailed parent sizes. This supplies a conditional order-flow benchmark, not a result already demonstrated by the current simulation.
- [Donier et al.](https://arxiv.org/abs/1412.0141): reduced reaction-diffusion impact limits. A future scaling comparison must establish its applicable regime; it is not guaranteed by sharing a DTRW lineage.

The uploaded long-paper bibliography has mixed CAM title/year/volume metadata; this supplement uses the publisher DOI metadata above. The uploaded manuscripts remain byte-for-byte unchanged. The new draft is an algorithm specification and experiment design, not scientific acceptance of numerical agreement with their limiting analysis.

## v0.5.1 scope

This patch retains the v0.5.0 numerical assessment and adds four full paired paths at a common operational time step. Field updates, physical child volume, sign tapes and measurement definitions are unchanged. The added source-support measurements do not feed back into the solver. Two focused tests check support masks and invariant paths under measurement/restart. The archived v0.5.0 F5 PDF was incomplete; this version regenerates it and checks that PDF export has completed before replacement.

The 18 finite assessment cases, 23 market-maker comparisons, 26 statistical benchmark paths and four primary trajectories are carried from v0.5.0 commit `a18779fb78fadcb0f6c8fe54c7ce8b08d3916bbe`, whose numerical recovery was checked. Their numeric arrays and tapes are preserved; current version identifiers and the test-count record are updated. The complete reproduction command can regenerate every case. Four new resolution paths and their diagnostic summaries are computed in this patch.

No prototype production module, new strategic agent, field equation, source smoothing, transport memory or observation clock is introduced. All F2–F6/V1 content comes from retained numerical trajectories or the declared input reference. The original manuscript ZIPs remain pinned and unchanged. Numerical acceptance remains open until the evidence supports it.
