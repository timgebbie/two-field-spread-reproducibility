# Numerical scope v0.3.0

This version implements the explicit Markov two-side-density recurrence and its causal completion/placement/execution state. It runs small numerical verification fixtures. The paper's full parameter study, retained meta-order curves, convergence assessment and animation are not yet complete.

No standalone theoretical figures or analytic teaching panels are required. An analytic formula is retained only when it independently tests a numerical component or supplies a justified overlay for an actual simulation comparison.

The registered configuration is dimensionless and illustrative. Its positive-reaction stationary field is obtained by the numerical recurrence, not substituted from an analytic reaction-off profile. The latter exists only inside a solver test. No empirical calibration, optimized market-maker strategy or universal impact law is claimed.

The model treats all imposed executions as initiations of opposite-side completion supply; reaction matching does not create new cohorts. Threshold prices, placement quotes and their inventory sampling times are distinct. The limitations in `ALGORITHM.md` apply before interpreting any subsequent figure.
