# v6.2.3 implementation notes

This change set closes the runtime contracts identified after the v6.2.2 repository audit.

## Contract closure

- module inputs and outputs use a catalogued producer-consumer graph;
- each subproblem stores its own primary/secondary task labels and validation capabilities;
- current and validated data/model hashes can invalidate stale downstream artifacts;
- AI cleanup produces the LaTeX source that is actually compiled.

## Executable validation

- the workbook writer and artifact checker share one canonical validator;
- capability flags drive constraint, equilibrium, conservation, discretization and convergence sheets;
- project-state semantics, deterministic workflow resolution and weighted review are executable scripts;
- compile profiles distinguish repository template entrypoints from final project entrypoints.

## Active package maintenance

- Nature assets are registered as optional visual references;
- active indexes and the manifest exclude archived legacy content except its pointer;
- static lint is separated from the Python 3.10–3.14 unit-test matrix;
- generated metadata refresh is restricted to `main`.

This document is maintenance documentation and is not part of the mathematical-modeling paper workflow.
