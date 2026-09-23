# v0.3.0 — Minimal two-density DTRW core

Implement explicit side-density transport, cancellation and reaction; causal geometric completion; inventory-referenced placement; capped price-priority execution; threshold observations; and fixed-reservoir volume accounting. Retain phase-labelled states and event records for later simulation figures and video.

Replace the standalone theory figures and plotting route with numerical verification. Remove the formula-only CSV outputs and Matplotlib/SciPy dependencies. NumPy is the only runtime dependency.

Fourteen numerical tests and two small integration fixtures pass. Final meta-order experiment selection and convergence assessment follow; this version does not present final scientific figures or impact claims.
