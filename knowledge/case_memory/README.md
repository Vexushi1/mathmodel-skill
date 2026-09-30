# D1 Case Memory corpus

The admission Authority is [schema.yaml](schema.yaml), including `x-admission`.
The actual consumer is [scripts/case_memory.py](../../scripts/case_memory.py).
The D1/D2 boundary follows [the evolution plan, section 9](../../docs/modeling_intelligence_evidence_evolution_plan.md#9-模块-dcase-memory).

`sources.json` contains independent source records. `cases.json` refers to a source
ID and its SHA-256 over canonical JSON: recursively normalize CRLF/CR to LF, sort
mapping keys, preserve array order, emit UTF-8 with compact separators and no
non-finite numbers. The source document never contains its own hash. Corpus
identity covers the parsed Schema, sources and cases using the same encoding;
formatting changes do not change that identity. Each operation separately reads
and rechecks original file bytes, so a change during inspection blocks its result.

The consumer pins the supported Schema semantic identity. Schema rule changes
require the protocol and supported identity to be reviewed together in one PR;
limits may be tightened within the fixed implementation ceilings. Schema keys
must be unambiguous and references must use local JSON pointers. D1 source
evidence matches the declared synthetic source section exactly after newline
normalization; this establishes text binding, not semantic truth.

The seven independently authored synthetic records cover prediction, evaluation,
continuous constrained optimization, conservation dynamics, network scheduling,
random simulation and a dependency across questions. Their failure conditions
are hypothetical migration counterexamples. Their baseline descriptions and
recommended checks have not been executed. `reviewed` records here declare an
`author_self_check` of synthetic content; they do not assert a native isolated
reviewer, human approval, empirical performance or a current project's validity.

Run the explicit read-only entrypoints from the repository root:

```text
python scripts/case_memory.py validate
python scripts/case_memory.py build-index
python scripts/case_memory.py check-index
```

Each command accepts `--corpus-root PATH`. `validate` reports admission and its
current byte read set. `build-index` returns deterministic JSON to stdout without
writing a file. `check-index` compares the existing index against current admitted
content and returns nonzero when missing or stale. The Python API additionally
supports an index path inside the selected corpus root. These operations have no
project writer and never execute text supplied by a case.

The canonical `index.json` is written only by
[scripts/generate_indexes.py](../../scripts/generate_indexes.py) through the
repository's GitHub `refresh-generated` workflow. Commit source changes and let
that workflow rebuild the index, navigation and MANIFEST. Its groups merge shared
source origins and identical decision cores after text whitespace/case
normalization. The representative is the smallest case ID. This bounded rule does
not establish general semantic duplicate detection; uncertain near duplicates
require a curator to resolve origin groups before setting a candidate to reviewed.

State, evidence, rights, publication screening, finite resource budgets and
withdrawal behavior are defined in `schema.yaml`. A state change does not make
private material safe for a public repository: keep real private candidates
outside this repository. Automated screening checks explicit path, account and
credential patterns; it cannot certify the absence of every personal name or
sensitive fact. Synthetic authorship and rights fields remain curator declarations,
not independent authorization proof. D1 rejects real-source admission even when a
record claims permission; that capability requires separately reviewed provenance
and authorization work.

To withdraw a public synthetic case, set `status` to `retired` and explain
`status_reason`, then rebuild through GitHub. The corpus identity changes and the
old derived index fails its freshness check. D1 neither queries models nor changes
any project qualification.

D2 provides bounded offline retrieval through
[scripts/case_memory_retrieve.py](../../scripts/case_memory_retrieve.py) (`query`),
using the separate
[retrieval Authority](../../core/case_memory_retrieval_contract.yaml).
[Usage and boundaries](../../packs/artifact/case_memory_retrieval.md) describe
typed conditions, explanatory matches, legal `no_match` and the distinct
`unavailable` state. Ordinary modeling routes do not load the corpus; synthetic
development-query results do not establish independent modeling performance.

[scripts/case_references.py](../../scripts/case_references.py) provides
`preview`, `record` and `inspect` for an explicit decision in the same question.
Preview and inspection are read-only; recording remains read-only unless writing
is explicitly requested. An authorized write uses the existing guarded project
transaction and changes only that question's references and state generation.
Changes to a referenced case, source or project context require review; references
do not grant model approval or accepted numerical qualification. The actual
implementation scope and evidence are recorded in the
[D2 plan](../../docs/modeling_intelligence_d2_execution_plan.md) and
[E2 handoff](../../docs/modeling_intelligence_e2_release_review_handoff.md).
