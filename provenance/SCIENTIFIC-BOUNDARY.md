# Scientific scope v0.2.0

This version implements controlled continuum-theory evaluators and renders their saved tables. The two figures show an exact reaction-off step-source reference and scalar whole-line response formulas. D=nu=1, kappa=0, unit exterior supply, placement width 12 and threshold 0.1 are declared dimensionless controls, not fitted market parameters.

The threshold spread is exact for this reaction-off reference. The paper's corresponding formula is conditional and asymptotic for the coupled positive-reaction model. Positive spread does not by itself establish the separation needed for dynamical reduction. Finite-width source attenuation is a spatially averaged density-response ratio, not a delivered-share fraction. Capacity is defined using window-average displacement rate.

No DTRW lattice, meta-order trajectory, endogenous market-maker feedback, nonlinear reaction experiment, convergence evidence for a solver or animation is implemented in v0.2.0. These are subsequent milestones toward v1.0.0. The final science gate has not occurred.

Inputs: TwoFieldSpread v1.1.9 and SpreadLetter v0.2.0, with the explicit numerical conventions recorded in the accepted v0.1.0 design. The original manuscripts remain private and unchanged. `EQUATION-MAP.md` identifies the equations and qualifications; `SOURCES.md` pins provenance.
