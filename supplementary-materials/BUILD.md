# Computational supplement — v1.0.0 rc1

This is the accepted 19-page computational supplement. Its PDF and LaTeX source are the exact revision accepted on 3 October 2026. The rc1 document label does not create a software release or tag; v1.0.0 remains deferred until the preprint is public.

From this directory, with pdfLaTeX and the packages listed in the source:

```bash
pdflatex -interaction=nonstopmode -halt-on-error SUPPLEMENTARY-MATERIAL-v1.0.0-rc1.tex
pdflatex -interaction=nonstopmode -halt-on-error SUPPLEMENTARY-MATERIAL-v1.0.0-rc1.tex
```

Repeat if the log requests another reference pass. The accompanying algorithm layout is required. The six files in `figures/` are byte-identical copies of the corresponding repository figures, included so that the accepted source builds unchanged from this directory. The video remains in the repository's root `figures/` directory.

The accepted build passed reference and layout checks, with all 19 pages visually inspected. No production numerical run was performed for this documentation revision. The historical v0.6.0 supplement remains in `provenance/`.

Accepted file SHA-256 values:

```text
PDF  09d5f87ae0494e1b5521017a89e32bba9c21fc3863a9fa4c7defb802fb47e3a9
TeX  32c67a2911f631f3dd376aa7fe5a1461b5829dd9262017e5a8576cc1d9c2211b
```
