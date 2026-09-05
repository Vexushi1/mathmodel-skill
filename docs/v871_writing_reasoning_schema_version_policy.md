# Writing Reasoning Schema Version Policy — v8.7.1 Decision Record

> Status: **ACTIVE MAINTENANCE DECISION / v8.7.1**  
> Applies to: `core/writing_reasoning_contract.yaml`  
> Current schema family: `1.8.0`  
> Decision: **keep `schema_version: 1.8.0` for v8.7.1**

## 1. Why this decision exists

The v8.7.1 read-path consistency audit found that `core/writing_reasoning_contract.yaml` remained at `schema_version: 1.8.0` while later Skill releases added additive semantic nodes such as Formula Role metadata and additional writing-governance fields. Several regression tests also assert the exact `1.8.0` value.

The question was therefore whether every additive semantic node should force a schema bump, or whether `schema_version` is the compatibility family for consumers that parse the contract.

## 2. Consumer audit

The v8.7.1 audit checked active repository consumers and found:

- runtime and validator behavior consume named semantic nodes directly;
- no active runtime/script was found that branches its parser or migration path on an exact Writing Reasoning schema value;
- exact `1.8.0` checks found in the active repository are regression tests protecting the compatible reasoning family and surrounding semantics, not parser-dispatch code;
- v8.7 Formula Role additions are additive: existing fields are not removed, renamed, retyped, or assigned incompatible meanings;
- v8.7.1 read-path hardening changes producer/consumer closure and state derivation; it does not redefine the existing Writing Reasoning data model incompatibly.

Accordingly, bumping to `1.9.0` only to mirror the Skill release would create churn without identifying a parser incompatibility.

## 3. Policy

`schema_version` is a **machine-consumer compatibility-family version**, not a mirror of the top-level Skill release and not a counter for every semantic addition.

### Bump the schema version when a consumer may need different parsing or migration behavior

Examples include:

- removing or renaming an existing machine-readable field;
- changing a field type or container shape incompatibly;
- changing an enum so that previously valid values become invalid or change meaning;
- moving an Authority node in a way that breaks existing pointer paths without a compatibility alias;
- changing required/optional semantics such that old consumers cannot safely read the contract;
- introducing a structural change that requires parser-version branching or migration logic.

Use semantic-version intent for the schema itself: compatible additive parser-facing changes may justify a schema minor version only when consumers are expected to detect or require the newer structure; incompatible parser behavior requires an appropriate major change.

### Do not bump the schema version for compatible semantic maintenance alone

Examples include:

- adding an optional/additive semantic node that old consumers can ignore safely;
- adding explanatory metadata or governance wording;
- adding a new consumer that reads existing fields without changing their contract;
- clarifying prose or examples without changing machine-readable meaning;
- closing producer/read-path/validator gaps around fields already valid in the current compatibility family.

## 4. v8.7.1 determination

For this patch:

```text
Writing Reasoning schema_version = 1.8.0
```

is intentionally retained.

The decision does **not** freeze the contract forever at 1.8.0. A future change that meets the parser/migration criteria above must review and bump the schema version rather than relying on this record as a permanent exemption.

## 5. Test intent

Historical regression tests may continue to assert `1.8.0` where they are explicitly protecting the current compatible reasoning family. A dedicated current-policy regression should additionally document that:

1. the active contract remains `1.8.0` for v8.7.1;
2. additive v8.7/v8.7.1 nodes do not themselves imply a bump;
3. no repository runtime parser is allowed to silently reinterpret the schema version as the top-level Skill release.

If a future schema bump is required, the bump PR should update the dedicated current-schema test and migrate historical exact-version assertions whose real purpose is semantic capability preservation rather than permanently pinning an old schema number.
