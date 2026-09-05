# v8.7.2 Active Template / Read-Path / Release Consistency Hardening Plan

> Status: **PLANNING / IMPLEMENTATION CONTEXT ONLY**  
> Base branch: `main`  
> Base commit at plan creation: `54bb66ce1174090580f9f6dbb703b9efd9bf2a75`  
> Current Skill release at plan creation: `8.7.1`  
> Target Skill release for implementation: `8.7.2`  
> Planned change level: `patch`  
> Working branch: `fix/v8.7.2-template-readpath-release-consistency`  
> This document is **not a Runtime Authority**. Current behavior remains owned by Bootstrap, active contracts, template manifests, validators and modules. If this plan conflicts with current `main`, current Authority wins and the plan must be updated before implementation.

---

## 1. Purpose

This plan records the repository-wide consistency repair identified after the v8.7.1 read-path / semantic-state hardening and the later AI-disclosure template edits.

The implementation goal is not to add new mathematical-modeling capability. It is to restore one coherent interpretation of the active Skill across:

- CUMCM Template Authority;
- executable LaTeX assembly;
- cross-file writing/handoff semantics;
- AI-disclosure compliance semantics;
- template validators and lint;
- active template version labels;
- fragment-level read-path validation;
- release carriers and Changelog;
- generated repository metadata and CI.

The target is a patch-level repair that preserves current public interfaces, project structure, user-execution boundaries and existing v8 compatibility.

---

## 2. Mandatory change brief

```text
修改主题：v8.7.2 Active Template / Read-Path / Release Consistency Hardening
当前版本：8.7.1
目标版本：8.7.2
变更等级：patch
直接目标：
  1. 修复 CUMCM Template Manifest 与真实 hsk_main.tex 顶层装配顺序漂移；
  2. 将 AI disclosure 从“模板硬编码项目事实”改为“当届规则 + 当前项目真实使用事实驱动”的合规槽位；
  3. 修复 Cross-File Chapter Handoff、README、测试与真实最终装配的顺序不一致；
  4. 加强模板 validator，使 undeclared active body input 无法绕过 Manifest Authority；
  5. 清理 active MCM/电工杯模板顶部容易被误读为 current Skill release 的旧版本号；
  6. 扩展保守的 fragment-level read-path health，覆盖真实 Markdown fragment links；
  7. 将 post-8.7.1 行为变化正式收束为 8.7.2 release，并同步 release carriers / Changelog。
明确不做：
  - 不修改数学建模方法、题型分类或模型选择规则；
  - 不修改 Problem Contract / Model Challenge / Human Model Approval；
  - 不修改 03A/03B 用户执行链、Workbook Schema、Project State Schema；
  - 不修改 MATLAB Figure Evidence ownership；
  - 不修改公开 CLI、目录命名、五文件默认布局；
  - 不把 MCM/ICM、电工杯或其他竞赛强行改造成 CUMCM 的章节结构；
  - 不根据未核验规则强制任何竞赛默认输出 AI 声明；
  - 不全仓盲目替换历史版本号；
  - 不修改 legacy/ 使其重新进入 active runtime。
权威事实源：
  - core/bootstrap.yaml
  - SKILL_CHANGE_GOVERNANCE.md
  - templates/latex/cumcm/hsk/template_manifest.yaml
  - core/writing_runtime_contract.yaml
  - modules/05_writing/paper_writing_protocol.md
  - config/competition_profiles.yaml
  - modules/06_review_delivery.md
  - scripts/validate_template_manifest.py
  - scripts/lint_skill.py + scripts/lint_skill_checks.py
预计修改文件：见本计划第 9 节
禁止触碰文件：见本计划第 10 节
兼容性要求：v8 旧项目继续可读；不自动重写已有论文正文；不新增 Project State / Workbook 必填字段
迁移要求：无强制数据迁移；仅新模板/后续写作按新 AI disclosure 槽位语义执行
验收测试：见本计划第 11 节
回滚方式：整 PR 回滚；无数据/schema migration，回滚不需要项目转换
```

---

## 3. Baseline facts and confirmed problems

### 3.1 CUMCM Template Authority and executable template are out of sync

Current `templates/latex/cumcm/hsk/template_manifest.yaml` declares itself the unique CUMCM Template Authority for the top-level paper skeleton and section order.

Its current default skeleton ends as:

```text
question_sections
→ evaluation
→ references
→ appendix
```

Current `templates/latex/cumcm/hsk/hsk_main.tex` actually assembles:

```text
question_sections
→ evaluation
→ sections/10_ai_tool_statement.tex
→ references
→ appendix
```

Therefore the Authority-declared assembly order and executable assembly order disagree.

### 3.2 Cross-file writing semantics still describe the pre-AI-disclosure final order

`modules/05_writing/paper_writing_protocol.md` currently treats the terminal structural seams as:

```text
模型评价 → 参考文献
参考文献 → 附录
```

The current executable template inserts an AI-disclosure file between evaluation and references, so final-order seam reasoning no longer matches the actual physical source order.

`tests/test_v810_cross_file_chapter_handoff.py` also reconstructs the default final order from the manifest and currently expects the old sequence without the AI-disclosure source.

### 3.3 Existing template validation has an undeclared-active-input blind spot

`scripts/validate_template_manifest.py` currently validates:

- declared slot sources exist;
- required question/example tokens exist;
- selected main-file tokens appear;
- selected tokens appear in the required relative order.

It does not prove that every active body-level `\\input` / `\\include` participating in the canonical default paper assembly is declared by `paper_skeleton.ordered_slots`.

As a result, a new active body source can be inserted between two already-ordered known tokens and still pass the validator.

The v8.7.2 patch must close this exact class of failure.

### 3.4 AI disclosure currently contains unverified project-specific factual claims

The active CUMCM and Diangong templates currently contain completed factual prose stating that the team used AI and listing concrete uses.

However current competition profiles keep current-edition rule fields, including `ai_disclosure`, in an unverified state until the current official rules are checked.

The final-review Authority already requires reconciliation among:

```text
verified current-edition rule
+ paper disclosure
+ supporting material
+ user-confirmed actual AI use
```

Therefore a reusable template must not silently invent the project fact “this team used AI in these ways”.

### 3.5 Reference exemplar provenance may have been contaminated by active-template changes

`templates/latex/cumcm/hsk/reference/example_mm_r1.tex` is declared as a stored adaptation/reference exemplar with provenance and a stored SHA-256.

The post-v8.7.1 AI-disclosure work also inserted the new declaration into that reference file and then refreshed its stored hash.

Before implementation, compare the file against the pre-AI-disclosure commit and decide whether the added declaration belongs to provenance/reference content. The expected default decision for this patch is:

- active-template behavior must not mutate a provenance exemplar merely to keep it visually synchronized;
- if the declaration was not part of the original/reference adaptation purpose, remove it from the exemplar and restore the provenance checksum to the verified reference-only content.

Do not guess the historical checksum; recover it from Git history during implementation.

### 3.6 Active template version-label hygiene is incomplete

Current active template headers include release-looking labels such as:

```text
HSK 电工杯 LaTeX 通用起稿模板 v7.6.0
HSK MCM/ICM LaTeX template v6.2.2
```

These are active files copied into new projects and can be mistaken for the current Skill release.

CUMCM already uses a safer pattern that explicitly marks old version numbers as architecture/template lineage only and points current release ownership elsewhere.

v8.7.2 should apply the same hygiene principle to other active templates.

### 3.7 `version: 6.2.3` in compile/competition profiles is ambiguous but should not be blindly renamed

`core/compile_profiles.yaml` and `config/competition_profiles.yaml` contain `version: 6.2.3`.

These are not current Skill release carriers under the active version lint. Renaming the field may break consumers and is unnecessary for a patch unless an actual parser problem is found.

Planned v8.7.2 treatment:

- keep the existing field for compatibility;
- add a concise comment or nearby documentation making clear that it is profile/config schema lineage, not the current Skill release;
- do not mass-update it to 8.7.2;
- defer any field rename/alias migration to a separately scoped compatibility change.

### 3.8 Fragment-level read-path health is strong but not complete

v8.7.1 validates fragment-level pointers for critical machine-like registries.

The remaining practical gap is ordinary Markdown links such as:

```text
[path label](../some/file.md#target-heading)
```

Current general repository-reference checking can prove the target file exists while not always proving the target heading/anchor exists.

v8.7.2 should add conservative fragment checking for real Markdown link syntax in active runtime surfaces, without turning every prose/code-form example into a machine pointer.

---

## 4. Authority decisions for v8.7.2

These decisions must remain stable during implementation unless new current-main evidence requires amending this plan first.

### 4.1 Template Manifest remains the sole CUMCM top-level assembly Authority

Do not introduce a second assembly-order registry.

`templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton.ordered_slots` remains authoritative for:

- top-level source order;
- required/conditional/repeatable slots;
- bibliography placement;
- appendix placement;
- AI-disclosure slot placement.

`hsk_main.tex`, README text and tests are consumers/implementations of this Authority.

### 4.2 AI disclosure is a compliance slot, not a modeling/writing fact invented by the template

The rule source is:

```text
config/competition_profiles.yaml
  → profiles.<competition>.edition_rules.ai_disclosure
```

The actual-use source must be current project/user-confirmed facts.

Final consistency remains governed by `modules/06_review_delivery.md` and `templates/review/final_review_matrix.yaml`.

The template may provide a location/scaffold, but must not assert unverified team behavior.

### 4.3 Default activation must be truth-bound

Because current edition rules are unverified in the repository, the generic reusable template must not make an unconditional factual AI-use statement.

Preferred patch semantics:

```text
AI disclosure slot exists in the template project
→ slot is structurally located immediately before references
→ visible/final disclosure content is activated/hydrated only from verified rule + actual-use facts
→ unresolved template placeholder cannot pass formal delivery
```

Implementation may choose either a commented conditional `\\input` or a non-factual scaffold file, but the acceptance criteria are fixed:

1. generic template compile must not fabricate actual AI use;
2. when disclosure is applicable, its final location is before references;
3. when applicable, final text must be project-specific and truth-bound;
4. when not applicable, no empty/fake declaration should appear in the final PDF;
5. a visible unresolved placeholder must fail formal audit/review.

### 4.4 No forced cross-competition synchronization

Do not add a MCM/ICM AI statement merely because CUMCM has an AI-disclosure slot.

Each competition follows its own verified current-edition rule.

Diangong's existing hard-coded factual statement should be converted to the same truth-bound template principle, but its paper structure remains independent of CUMCM.

### 4.5 Release-carrier versions and schema/config versions remain distinct

Current Skill release remains controlled by the explicit release carriers already checked by `scripts/lint_skill.py`.

Subordinate schema/config versions are not rewritten unless their own schema changes.

---

## 5. Planned implementation phases

## Phase A — CUMCM Template Authority closure

### A1. Add an explicit AI-disclosure slot to the manifest

Modify `templates/latex/cumcm/hsk/template_manifest.yaml` so the ordered skeleton explicitly includes the AI-disclosure capability between evaluation and references.

Conceptual order:

```text
evaluation
→ ai_disclosure [conditional/truth-bound]
→ references
→ appendix
```

The exact fields must reuse existing slot semantics where possible. Avoid a new schema version unless existing `required/default_active/activation/note` fields cannot express the behavior.

### A2. Make `hsk_main.tex` consume the manifest decision

Align the canonical main file with the slot activation decision.

If the slot is conditional by default, the main file must visibly encode that condition (for example through a commented input plus clear activation comment) instead of silently keeping an unconditional factual section.

### A3. Update fixed-template checks without creating a second Authority

The manifest's smoke-test tokens may be updated to include the AI-disclosure placement, but they must remain explicitly secondary to `paper_skeleton.ordered_slots`.

Do not add another standalone hard-coded order table in another file.

---

## Phase B — AI-disclosure factual-boundary repair

### B1. CUMCM statement source

Modify `templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex` so it is a safe reusable scaffold, not a completed assertion about every future team.

Requirements:

- no unconditional claim that AI was used;
- no unconditional list of uses such as language polishing/code debugging unless confirmed for the current project;
- clear source comments identifying competition rule and project actual-use facts as prerequisites;
- no duplicate full compliance policy inside the file;
- final visible statement must be compatible with the existing final-review `ai_disclosure` family.

### B2. Diangong statement source

Apply the same truth-bound principle to `templates/latex/diangong/main.tex`.

Do not force identical wording; only the factual-boundary rule is shared.

### B3. MCM/ICM

Do not add an AI statement by default unless current verified MCM/ICM rules require it.

Only clean the active template's release-looking header in this patch.

### B4. Formal-audit placeholder behavior

Inspect existing placeholder/TODO detection in the formal LaTeX audit chain.

Preferred order:

1. reuse an existing deterministic placeholder failure if it already covers the chosen AI-disclosure scaffold;
2. otherwise add the smallest explicit sentinel check needed to prevent unresolved visible AI-disclosure placeholder text from passing formal delivery;
3. do not add a broad new “AI detector”.

Potential affected scripts, only if required:

- `scripts/audit_latex_project.py`
- `scripts/audit_paper_prose.py`

No statistical authorship/AI-origin detection is allowed.

---

## Phase C — Cross-file final-order and documentation synchronization

### C1. CUMCM README

Update `templates/latex/cumcm/hsk/README.md` so all three representations agree:

- recommended chapter skeleton;
- modular project tree;
- progressive writing/final assembly explanation.

The AI-disclosure slot must be shown as conditional/truth-bound, not as an unconditional project fact.

### C2. Paper Writing Protocol

Update `modules/05_writing/paper_writing_protocol.md` terminal seam semantics.

Expected model:

```text
if ai_disclosure active:
  evaluation → ai_disclosure → references → appendix
else:
  evaluation → references → appendix
```

The existing `structural_terminal` profile should be reused unless a genuinely distinct semantic behavior is necessary. Do not introduce a new profile only to rename the same “no narrative bridge required” behavior.

### C3. Writing Runtime Contract

Inspect `core/writing_runtime_contract.yaml` for explicit assumptions about the old final order.

Only modify it if required for:

- active-final-assembly resolution;
- seam calculation;
- AI-disclosure activation facts;
- explicit source pointers that would otherwise remain stale.

Do not duplicate the manifest's complete slot list into runtime.

---

## Phase D — Template validator hardening

Modify `scripts/validate_template_manifest.py` to detect undeclared active body composition.

### D1. Exact default assembly invariant

The validator should be able to prove that the canonical default body assembly corresponds to manifest-declared active/default slots in the same order.

It must distinguish:

- infrastructure inputs before body assembly (`config/preamble`, commands, metadata);
- body/top-level paper inputs controlled by the manifest;
- commented conditional inputs;
- bibliography command;
- appendix input.

### D2. Reject undeclared active body sources

A new active `\\input` / `\\include` added to the canonical body between declared slots must fail validation unless represented by a manifest slot or explicitly allowed infrastructure mechanism.

This is the specific regression that current v8.7.1 validation misses.

### D3. Do not overfit to one literal file list

The validator must continue supporting:

- repeatable question sections;
- default-inactive data/model-preparation slots;
- future Q4+ comments/examples;
- modular LaTeX;
- existing manifest schema compatibility.

### D4. Preserve the manifest as Authority

Prefer deriving expected assembly from `paper_skeleton.ordered_slots` and existing activation semantics rather than maintaining another independent Python constant with the same full order.

---

## Phase E — Regression tests for assembly and handoff

### E1. Update existing template Authority tests

Likely affected:

- `tests/test_v800_template_authority.py`
- `tests/test_v810_cross_file_chapter_handoff.py`

Required assertions:

- manifest contains the AI-disclosure slot in the correct location;
- default active-source resolution reflects the chosen activation policy;
- when AI disclosure is active, final adjacency includes it;
- when inactive, evaluation directly precedes references;
- bibliography and appendix placement remain unchanged;
- CUMCM question structure remains adaptive and unaffected.

### E2. Add a v8.7.2 validator regression

Add a focused behavior test, preferably a new file such as:

```text
tests/test_v872_template_assembly_consistency.py
```

It must prove at least:

1. current canonical manifest/template passes;
2. a synthetic undeclared active body `\\input` fails;
3. a commented conditional input does not count as active;
4. declared conditional AI-disclosure activation can be validated;
5. infrastructure inputs are not misclassified as paper skeleton slots.

Do not satisfy this test by weakening existing checks.

---

## Phase F — Active release-label hygiene

### F1. Diangong template

Change the first-line release-looking label to a release-neutral active template title.

If historical lineage must be retained, use an explicit provenance-only comment analogous to the CUMCM pattern.

### F2. MCM/ICM template

Apply the same treatment.

### F3. Regression coverage

Extend the existing v8.7.1 active-release-label hygiene test or add v8.7.2 coverage so active template headers cannot again present old lineage numbers as ambiguous current release labels.

The test should distinguish:

- allowed explicit provenance/lineage text;
- forbidden ambiguous active-template version branding.

### F4. Compile/competition profile version comments

Add concise clarification around `version: 6.2.3` if needed, but retain the field/value for compatibility.

Do not rename or bump this field as part of the Skill release bump.

---

## Phase G — Markdown fragment read-path coverage

Extend repository-reference health conservatively.

### G1. Scope

Validate fragment targets for actual Markdown link syntax in active runtime surfaces, including:

```markdown
[Authority](../path/file.md#heading)
[Local section](#heading)
```

### G2. Reuse heading normalization

Reuse the existing v8.7.1 Markdown heading normalization logic where possible so numbered headings and punctuation changes are handled consistently.

Do not invent a second slug/fragment algorithm unless required.

### G3. Avoid free-text false positives

Do **not** blindly treat every inline-code string containing `#` as a mandatory pointer.

Keep two layers:

- critical machine-like registries: existing strict fragment scan;
- real Markdown links: new fragment validation;
- free prose/examples: not automatically promoted to runtime pointer status.

### G4. Regression tests

Add tests for:

- valid same-file heading fragment;
- valid relative cross-file heading fragment;
- missing heading fragment;
- missing file;
- external URL fragment ignored by repository-local validator;
- historical/legacy prose remaining outside default active scan.

---

## Phase H — Reference exemplar provenance repair

Before changing the reference file, use Git history to compare:

```text
pre-AI-disclosure exemplar
vs
current exemplar
```

If the only added semantic content is the new AI declaration and it was not part of the original stored adaptation purpose:

1. remove the declaration from `reference/example_mm_r1.tex`;
2. restore the stored adaptation to reference-only semantics;
3. update `template_manifest.yaml.reference_provenance.user_template_source.stored_sha256` to the verified restored file hash;
4. keep the original `source_sha256` unchanged;
5. add a regression proving active-template changes do not require mutating the reference exemplar.

Do not copy current active policy into provenance/reference files.

---

## Phase I — Release-state closure to 8.7.2

Only after the semantic/template/validator changes are stable, bump the Skill patch release from `8.7.1` to `8.7.2`.

### I1. Update only declared release carriers

Use current lint/version contracts rather than global search-and-replace.

Expected release carriers include:

- `core/bootstrap.yaml`
- `.codex-plugin/plugin.json`
- `core/workflow_router.yaml`
- `core/module_manifest.yaml`
- `core/output_contract.yaml`
- `SKILL.md`
- `skills/mathmodel-skill/SKILL.md`
- `README.md`
- `core/hsk_core_policy.md`
- `CHANGELOG.md`

Verify the exact current carrier list from `scripts/lint_skill_checks.py` before editing.

### I2. Preserve root/package Skill byte parity

`SKILL.md` and `skills/mathmodel-skill/SKILL.md` must remain byte-identical.

Do not separately hand-maintain divergent summaries.

### I3. Changelog entry

The v8.7.2 Changelog should state the actual patch behavior, including:

- Template Manifest ↔ canonical LaTeX assembly closure;
- truth-bound AI-disclosure slot semantics;
- undeclared-active-input validator hardening;
- cross-file seam synchronization;
- active template release-label hygiene;
- conservative Markdown fragment-link validation;
- no change to model mathematics, execution/workbook/project-state schemas or public CLI.

### I4. Do not bump subordinate schemas without schema changes

Do not change:

- Workbook schema version;
- Project State schema version;
- Writing Reasoning schema family;
- compile/competition profile `version: 6.2.3` merely to match 8.7.2.

---

## 6. AI-disclosure state model to preserve

Implementation should follow this conceptual state machine without necessarily adding new persisted fields:

```text
competition edition rule
        |
        v
verified? ---------------- no ----------------> do not claim official requirement
   |
  yes
   |
   v
rule requires/allows disclosure?
   |
   +---- no/none ----> no forced template disclosure
   |
   +---- yes --------> collect current project actual-use facts
                            |
                            v
                     facts confirmed?
                        |
                     no |----> unresolved / fail final compliance
                        |
                       yes
                        |
                        v
                  render project-specific disclosure
                        |
                        v
             final-review ai_disclosure reconciliation
```

Important boundaries:

- no authorship inference;
- no “AI-like” text detector;
- no assumption that AI was or was not used based on writing style;
- no fabricated interaction history;
- no template-level claim that all teams use the same tools/purposes;
- no unverified competition rule presented as official.

---

## 7. Compatibility and migration policy

### 7.1 Existing v8 projects

- remain readable;
- are not automatically rewritten;
- existing accepted workbooks/project state remain valid unless independently stale for their existing reasons;
- no model re-approval is triggered by pure template/compliance wording changes;
- no numerical recomputation is triggered by this patch.

### 7.2 Existing papers that already contain an AI disclosure

Do not automatically delete or rewrite user/project text.

On the next writing/final-review route:

- treat existing disclosure as project content;
- reconcile it with current verified rule and actual-use facts;
- edit only if it is false, incomplete, unverified or inconsistent.

### 7.3 New template copies

New copies should receive the repaired truth-bound scaffold/activation semantics.

### 7.4 Legacy

No new default runtime dependency on `legacy/`.

Historical templates remain historical evidence only.

---

## 8. Rollback strategy

Because this patch should not introduce a data/schema migration, rollback is repository-level only.

If v8.7.2 causes an unexpected regression:

1. revert the single-theme PR;
2. regenerate repository metadata from the reverted source tree;
3. rerun lint, full unit tests and affected LaTeX compile jobs;
4. restore the prior release state through a normal patch/revert release process if 8.7.2 was already published;
5. do not manually restore MANIFEST hashes.

No project workbook/state conversion should be necessary.

---

## 9. Expected implementation file set

This is an impact forecast, not permission to modify every file automatically.

### 9.1 Expected source/Authority changes

```text
templates/latex/cumcm/hsk/template_manifest.yaml
templates/latex/cumcm/hsk/hsk_main.tex
templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex
templates/latex/cumcm/hsk/README.md
modules/05_writing/paper_writing_protocol.md
scripts/validate_template_manifest.py
templates/latex/diangong/main.tex
templates/latex/mcm/main.tex
```

### 9.2 Conditional source changes after inspection

```text
core/writing_runtime_contract.yaml
config/competition_profiles.yaml
core/compile_profiles.yaml
scripts/lint_skill.py
scripts/lint_skill_checks.py
scripts/audit_latex_project.py
scripts/audit_paper_prose.py
templates/latex/cumcm/hsk/reference/example_mm_r1.tex
```

Only modify a conditional file when the implementation evidence shows a real dependency.

### 9.3 Expected tests

```text
tests/test_v800_template_authority.py
tests/test_v810_cross_file_chapter_handoff.py
tests/test_v871_active_release_label_hygiene.py
tests/test_v871_fragment_health.py
tests/test_v872_template_assembly_consistency.py   # likely new
```

Additional existing tests may require updates if their fixture explicitly encodes the old assembly order.

### 9.4 Release carriers for final 8.7.2 closure

```text
core/bootstrap.yaml
.codex-plugin/plugin.json
core/workflow_router.yaml
core/module_manifest.yaml
core/output_contract.yaml
SKILL.md
skills/mathmodel-skill/SKILL.md
README.md
core/hsk_core_policy.md
CHANGELOG.md
```

Confirm against current lint before editing.

### 9.5 Generated files

Do not hand edit. The feature-branch workflow is expected to regenerate as required:

```text
SKILL_FILE_INDEX.md
TEMPLATE_INDEX.md
HSK_SKILL_FILE_INDEX_V622.md
HSK_TEMPLATE_INDEX_V622.md
MANIFEST.sha256
```

Review the generated diff after automation.

---

## 10. Explicit no-touch / no-scope-expansion list

Unless a newly discovered direct dependency makes a change unavoidable and this plan is amended first, do not change:

```text
core/project_state.schema.yaml
core/workbook_schema.yaml
core/model_approval_contract.yaml
core/numerical_verification_contract.yaml
core/global_preprocessing_contract.yaml
core/user_execution_contract.yaml
modules/01_problem_audit.md
modules/02_model_design.md
modules/03_data_preprocessing.md
modules/03_solve_validate.md
modules/03_result_analysis.md
modules/04_figure_evidence.md
packs/task/*
legacy/*
```

Do not introduce:

- new model-selection rules;
- new numerical validation semantics;
- new project-state fields;
- new workbook sheets;
- new public CLI parameters;
- new submission package formats;
- new AI-detection heuristics.

---

## 11. Acceptance and test matrix

### 11.1 Governance baseline

Before implementation writes:

- re-read current `main` Bootstrap and governance;
- confirm target branch is based on current `main` or rebase/rebuild if `main` moved;
- search overlapping open PRs again;
- amend this plan if the baseline changed materially.

### 11.2 Mandatory repository tests

Run:

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

### 11.3 Template-specific tests

Run:

```bash
python scripts/validate_template_manifest.py templates/latex/cumcm/hsk/template_manifest.yaml
```

Then run/confirm CI compile jobs for:

```text
LaTeX CUMCM
LaTeX Diangong
LaTeX MCM-ICM
Production LaTeX attestation
```

### 11.4 Read-path regression criteria

Pass only if:

- all critical Authority fragments resolve;
- real active Markdown fragment links resolve;
- missing-fragment synthetic tests fail as expected;
- no false dependency on `legacy/` is introduced.

### 11.5 Template Authority regression criteria

Pass only if:

- manifest and canonical main default assembly agree;
- undeclared active body input is rejected;
- conditional inactive input is not treated as active;
- AI-disclosure position is deterministic when active;
- references and appendix remain in the correct relative order.

### 11.6 AI-disclosure regression criteria

Pass only if:

- generic templates do not fabricate actual team AI use;
- unverified competition rules are not presented as official requirements;
- active disclosure can be rendered before references when applicable;
- unresolved visible disclosure placeholders cannot pass formal delivery;
- no authorship/AI-origin inference is added.

### 11.7 Version regression criteria

Pass only if:

- every declared Skill release carrier reads 8.7.2;
- root/package `SKILL.md` remain byte-identical;
- subordinate schema/config versions are unchanged unless their schema changed;
- active MCM/Diangong template headers no longer ambiguously brand themselves as old current Skill releases;
- Changelog accurately describes v8.7.2 behavior.

### 11.8 Generated metadata criteria

Pass only if:

- generator-produced changes come from `scripts/generate_indexes.py` / the branch workflow;
- no MANIFEST hash is manually fabricated;
- `generate_indexes.py --check` is clean on the final branch head.

---

## 12. Definition of Done

The patch is complete only when all of the following are true:

- [ ] CUMCM Manifest explicitly models the AI-disclosure position/capability.
- [ ] Canonical `hsk_main.tex` matches the Manifest's default/conditional assembly semantics.
- [ ] CUMCM README matches the real assembly and file tree.
- [ ] Cross-file handoff semantics handle active/inactive AI disclosure correctly.
- [ ] AI-disclosure template content no longer invents project facts.
- [ ] Diangong follows the same factual-boundary principle.
- [ ] MCM/ICM is not given a forced AI statement without verified rule evidence.
- [ ] Manifest validator rejects undeclared active body inputs.
- [ ] Relevant behavior-level tests cover the previous blind spot.
- [ ] Reference exemplar provenance has been reviewed and repaired if contaminated.
- [ ] Active MCM/Diangong release-looking headers are release-neutral/provenance-explicit.
- [ ] Real active Markdown fragment links receive fragment-level health validation.
- [ ] Skill release carriers are synchronized at 8.7.2.
- [ ] Changelog contains the 8.7.2 patch entry.
- [ ] Root/package Skill parity passes.
- [ ] Full unit suite passes.
- [ ] CUMCM/Diangong/MCM compile jobs pass.
- [ ] Production LaTeX attestation passes.
- [ ] Generated metadata check passes.
- [ ] PR contains no unrelated refactor or legacy rewrite.

---

## 13. Future-chat / context-resume protocol

This document exists specifically so a later conversation can recover the intended repair without relying on chat memory.

When resuming work:

1. read current `main:core/bootstrap.yaml`;
2. read current `main:SKILL_CHANGE_GOVERNANCE.md`;
3. read this plan;
4. inspect the current branch/PR head and compare it with current `main`;
5. search for overlapping open PRs;
6. re-fetch the Authority files relevant to the next implementation phase;
7. treat this plan as intent/context only, never as stronger than current Authority;
8. update this plan before implementation if current facts invalidate any planned step;
9. continue on the same branch only when this conversation is explicitly continuing the same v8.7.2 task; otherwise follow governance for branch ownership.

Recommended implementation order after this planning commit:

```text
A. Manifest/assembly closure
→ B. AI factual-boundary repair
→ C. handoff/docs synchronization
→ D. validator hardening
→ E. behavior tests
→ F. release-label hygiene
→ G. Markdown fragment coverage
→ H. reference provenance verification/repair
→ I. 8.7.2 release-carrier closure
→ generated metadata
→ full CI
```

Do not bump to 8.7.2 first and then discover the semantic scope later. The version bump is the final release-state closure after the patch behavior is stable.

---

## 14. Planning status at creation

At the time this plan was created:

- current default branch: `main`;
- current main baseline used: `54bb66ce1174090580f9f6dbb703b9efd9bf2a75`;
- current Skill version: `8.7.1`;
- no overlapping open PR was found for the v8.7.2/template consistency scope;
- current branch was created specifically for this single repair theme;
- no Runtime Authority or executable behavior was modified by this planning document itself.

The next step is implementation against this plan, not another broad repository redesign.
