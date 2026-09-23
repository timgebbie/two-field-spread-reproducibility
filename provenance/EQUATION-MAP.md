# Theory equation map v0.2.0

Source: supplied `CATG-TwoFieldSpread-v1.1.9.tex`. Function names below refer to `functions/theory.py`.

| Evaluator / output | Source equation or derivation | Retained conditions |
|---|---|---|
| `stationary_step`; Figure 1 | `eq:stationaryBid`, `eq:stationaryAsk`, specialized to zero reaction and constant exterior step supply | Exact infinite-line control; equal lit/latent amplitudes and lengths give a constant sum outside each placement quote; no completion prehistory |
| `penetration`; theory (d,e) | `eq:penetrationDepth`, `eq:spreadDecomposition`, `eq:logThresholdSensitivity` | Positive cancellation, threshold below own edge density, ordered inward crossings. Exact for the chosen reaction-off reference; conditional leading order in the full model |
| `heat_kernel`; theory (a) | `eq:offsetKernel` | Frozen geometry, whole line, positive operational lag, linear transport/cancellation |
| `uniform_kernel`; theory (a) | Spatial convolution of `eq:offsetKernel` with normalized uniform outward supply | Actual source width retained; does not replace the source by its endpoint |
| `peak_lag`; theory (b) | `eq:dampedPeakLag`, `eq:peakLagLimit` | Point source, positive offset; no positive interior peak at zero offset |
| `integrated_attenuation`; theory (c) | `eq:replenishmentSuppression`, with source-shape integration | nu>0; integrated density response, not volume accounting. Width zero is the point-source limit |
| `window_response`, `window_capacity`; theory (f) | Finite-window capacity test and `eq:nonlocalCapacityScaling` | Direct same-side constant depletion, frozen positive slope magnitude; no displaced net-current substitution |

For uniform outward width w, the exact scalar kernel is

$$K_{d,w}(t)=\frac{e^{-\nu t}}{2w}\left[\operatorname{erfc}\!\left(\frac{d}{\sqrt{4Dt}}\right)-\operatorname{erfc}\!\left(\frac{d+w}{\sqrt{4Dt}}\right)\right].$$

The implementation evaluates the Gaussian-tail difference in log space. Its integral relative to the direct point response is

$$R_{d,w}=e^{-d/\ell_\nu}\frac{\ell_\nu}{w}(1-e^{-w/\ell_\nu}),\qquad \ell_\nu=\sqrt{D/\nu}.$$

For a constant direct current, C(T) is displacement per unit current and

$$C(T)=\frac{\operatorname{erf}(\sqrt{\nu T})}{2\lambda\sqrt{D\nu}},\qquad L_{avg}(T)=T/C(T).$$

At nu=0, C(T)=sqrt(T)/(lambda sqrt(pi D)); hence L_avg=lambda sqrt(pi D T). The reciprocal instantaneous endpoint response rate gives L_end=2 L_avg in that zero-cancellation control. The two conventions are labelled separately.

Independent verification uses spatial/time quadrature, scalar optimization, finite-difference stationary residuals away from the source step, numerical threshold roots and limiting cases. These checks validate evaluators; they are not convergence tests of a lattice solver.
